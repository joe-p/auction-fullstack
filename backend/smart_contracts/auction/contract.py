import beaker
import pyteal as pt


class AuctionState:
    previous_bidder = beaker.GlobalStateValue(
        stack_type=pt.TealType.bytes,
        default=pt.Bytes(""),
        descr="Address of the highest bidder",
    )

    auction_end = beaker.GlobalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(0),
        descr="Timestamp of the end of the auction",
    )

    previous_bid = beaker.GlobalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(0),
        descr="Amount of the highest bid (uALGO)",
    )

    asa_amt = beaker.GlobalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(0),
        descr="Total amount of ASA being auctioned",
    )

    asa = beaker.GlobalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(0),
        descr="ID of the ASA being auctioned",
    )

    claimable_amount = beaker.LocalStateValue(
        stack_type=pt.TealType.uint64,
        default=pt.Int(0),
        descr="Amount this account can claim"
    )


app = beaker.Application("Auction", state=AuctionState)


@app.create(bare=True)
def create() -> pt.Expr:
    # Set all global state to the default values
    return app.initialize_global_state()


# Only allow app creator to opt the app account into a ASA
@app.external(authorize=beaker.Authorize.only(pt.Global.creator_address()))
def opt_into_asset(asset: pt.abi.Asset) -> pt.Expr:
    return pt.Seq(
        # Verify a ASA hasn't already been opted into
        pt.Assert(app.state.asa == pt.Int(0)),
        # Save ASA ID in global state
        app.state.asa.set(asset.asset_id()),
        # Submit opt-in transaction: 0 asset transfer to self
        pt.InnerTxnBuilder.Execute(
            {
                pt.TxnField.type_enum: pt.TxnType.AssetTransfer,
                pt.TxnField.fee: pt.Int(0),  # cover fee with outer txn
                pt.TxnField.asset_receiver: pt.Global.current_application_address(),
                pt.TxnField.xfer_asset: asset.asset_id(),
                pt.TxnField.asset_amount: pt.Int(0),
            }
        ),
    )


@app.external(authorize=beaker.Authorize.only(pt.Global.creator_address()))
def start_auction(
    starting_price: pt.abi.Uint64,
    length: pt.abi.Uint64,
    axfer: pt.abi.AssetTransferTransaction,
) -> pt.Expr:
    return pt.Seq(
        # Ensure the auction hasn't already been started
        pt.Assert(app.state.auction_end.get() == pt.Int(0)),
        # Verify axfer
        pt.Assert(axfer.get().asset_receiver() == pt.Global.current_application_address()),
        pt.Assert(axfer.get().xfer_asset() == app.state.asa),
        # Set global state
        app.state.asa_amt.set(axfer.get().asset_amount()),
        app.state.auction_end.set(pt.Global.latest_timestamp() + length.get()),
        app.state.previous_bid.set(starting_price.get()),
    )


@pt.Subroutine(pt.TealType.none)
def pay(receiver: pt.Expr, amount: pt.Expr) -> pt.Expr:
    return pt.InnerTxnBuilder.Execute(
        {
            pt.TxnField.type_enum: pt.TxnType.Payment,
            pt.TxnField.receiver: receiver,
            pt.TxnField.amount: amount,
            pt.TxnField.fee: pt.Int(0),  # cover fee with outer txn
        }
    )

@app.opt_in(bare=True)
def opt_into_app():
    return app.state.claimable_amount[pt.Txn.sender()].set_default()

@app.external
def bid(payment: pt.abi.PaymentTransaction) -> pt.Expr:
    return pt.Seq(
        # Ensure auction hasn't ended
        pt.Assert(pt.Global.latest_timestamp() < app.state.auction_end.get()),
        # Verify payment transaction
        pt.Assert(payment.get().amount() > app.state.previous_bid.get()),
        pt.Assert(pt.Txn.sender() == payment.get().sender()),
        pt.Assert(payment.get().receiver() == pt.Global.current_application_address()),
        app.state.claimable_amount[pt.Txn.sender()].set(
            app.state.claimable_amount[pt.Txn.sender()] + payment.get().amount()
        ),
        # Set global state
        app.state.previous_bid.set(payment.get().amount()),
        app.state.previous_bidder.set(payment.get().sender()),
    )


@app.external
def claim_bids() -> pt.Expr:
    claimable_amount = app.state.claimable_amount[pt.Txn.sender()]
    return pt.Seq(
        pt.If(pt.Txn.sender() == app.state.previous_bidder.get()).
        Then(pay(pt.Txn.sender(), claimable_amount - app.state.previous_bid.get())).
        Else(pay(pt.Txn.sender(), claimable_amount))
    )


@app.external
def claim_asset(asset: pt.abi.Asset) -> pt.Expr:
    return pt.Seq(
        pt.Assert(pt.Global.latest_timestamp() > app.state.auction_end.get()),
        # Send ASA to highest bidder
        pt.InnerTxnBuilder.Execute(
            {
                pt.TxnField.type_enum: pt.TxnType.AssetTransfer,
                pt.TxnField.fee: pt.Int(0),  # cover fee with outer txn
                pt.TxnField.xfer_asset: app.state.asa,
                pt.TxnField.asset_amount: app.state.asa_amt,
                pt.TxnField.asset_receiver: app.state.previous_bidder,
                pt.TxnField.asset_close_to: app.state.previous_bidder,
            }
        ),
    )


@app.delete
def delete() -> pt.Expr:
    return pt.InnerTxnBuilder.Execute(
        {
            pt.TxnField.type_enum: pt.TxnType.Payment,
            pt.TxnField.fee: pt.Int(0),  # cover fee with outer txn
            pt.TxnField.receiver: pt.Global.creator_address(),
            # close_remainder_to to sends full balance, including 0.1 account MBR
            pt.TxnField.close_remainder_to: pt.Global.creator_address(),
            # we are closing the account, so amount can be zero
            pt.TxnField.amount: pt.Int(0),
        }
    )


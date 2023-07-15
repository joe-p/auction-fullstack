import { WalletProvider, useWallet } from '@txnlab/use-wallet'
import { SnackbarProvider } from 'notistack'
import { useState } from 'react'
import AppCalls from './components/AppCalls'
import ConnectWallet from './components/ConnectWallet'
import Transact from './components/Transact'
import { useAlgoWallet } from './hooks/useAlgoWalletProvider'
import { getAlgodConfigFromViteEnvironment } from './utils/network/getAlgoClientConfigs'

enum AuctionState {
  Pending,
  Created,
  Started,
  Ended,
}

export default function App() {
  const [openWalletModal, setOpenWalletModal] = useState<boolean>(false)
  const [openDemoModal, setOpenDemoModal] = useState<boolean>(false)
  const [appCallsDemoModal, setAppCallsDemoModal] = useState<boolean>(false)
  const [auctionState, setAuctionState] = useState<AuctionState>(AuctionState.Pending)
  const { activeAddress } = useWallet()

  const toggleWalletModal = () => {
    setOpenWalletModal(!openWalletModal)
  }

  const createApp = () => {
    setAuctionState(AuctionState.Created)
  }

  const startAuction = () => {
    setAuctionState(AuctionState.Started)
  }

  const algodConfig = getAlgodConfigFromViteEnvironment()

  const walletProviders = useAlgoWallet({
    nodeToken: String(algodConfig.token),
    nodeServer: algodConfig.server,
    nodePort: String(algodConfig.port),
    network: algodConfig.network,
    autoConnect: true,
  })

  return (
    <SnackbarProvider maxSnack={3}>
      <WalletProvider value={walletProviders.walletProviders}>
        <div className="hero min-h-screen bg-teal-400">
          <div className="hero-content text-center rounded-lg p-6 max-w-md bg-white mx-auto">
            <div className="max-w-md">
              <h1 className="text-4xl">
                Welcome to <div className="font-bold">AlgoKit 🙂</div>
              </h1>
              <p className="py-6">
                This starter has been generated using official AlgoKit React template. Refer to the resource below for next steps.
              </p>

              <div className="grid">
                <button data-test-id="connect-wallet" className="btn m-2" onClick={toggleWalletModal}>
                  Wallet Connection
                </button>

                {activeAddress && auctionState === AuctionState.Pending && (
                  <button className="btn m-2" onClick={createApp}>
                    Create App
                  </button>
                )}

                {activeAddress && auctionState === AuctionState.Created && (
                  <label htmlFor="asa" className="label m-2">
                    Asset ID
                  </label>
                )}
                {activeAddress && auctionState === AuctionState.Created && (
                  <input type="number" id="asa" value="0" className="input input-bordered" />
                )}

                {activeAddress && auctionState === AuctionState.Created && (
                  <label htmlFor="asa-amount" className="label m-2">
                    Asset Amount
                  </label>
                )}
                {activeAddress && auctionState === AuctionState.Created && (
                  <input type="number" id="asa-amount" value="0" className="input input-bordered" />
                )}

                {activeAddress && auctionState === AuctionState.Created && (
                  <label htmlFor="start" className="label m-2">
                    Start Amount
                  </label>
                )}
                {activeAddress && auctionState === AuctionState.Created && (
                  <input type="number" id="start" value="0" className="input input-bordered" />
                )}

                {activeAddress && auctionState === AuctionState.Created && (
                  <button className="btn m-2" onClick={startAuction}>
                    Start Auction
                  </button>
                )}

                {activeAddress && auctionState === AuctionState.Started && (
                  <label htmlFor="bid" className="label m-2">
                    Bid Amount
                  </label>
                )}
                {activeAddress && auctionState === AuctionState.Started && (
                  <input type="number" id="bid" value="0" className="input input-bordered" />
                )}

                {activeAddress && auctionState === AuctionState.Started && <button className="btn m-2">Bid</button>}
              </div>

              <ConnectWallet openModal={openWalletModal} closeModal={toggleWalletModal} />
              <Transact openModal={openDemoModal} setModalState={setOpenDemoModal} />
              <AppCalls openModal={appCallsDemoModal} setModalState={setAppCallsDemoModal} />
            </div>
          </div>
        </div>
      </WalletProvider>
    </SnackbarProvider>
  )
}

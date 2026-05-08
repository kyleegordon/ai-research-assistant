import UploadPanel from './features/upload/UploadPanel'
import ChatWindow from './features/chat/ChatWindow'
import styles from './App.module.css'

export default function App() {
  return (
    <div className={styles.layout}>
      <aside className={styles.sidebar}>
        <UploadPanel />
      </aside>
      <main className={styles.main}>
        <ChatWindow />
      </main>
    </div>
  )
}

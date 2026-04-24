export default function Toast({ message, tone = 'success', onClose }) {
  if (!message) return null

  return (
    <div className={`toast toast--${tone}`}>
      <span>{message}</span>
      <button onClick={onClose}>✕</button>
    </div>
  )
}

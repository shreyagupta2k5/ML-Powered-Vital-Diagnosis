export default function LoadingSpinner({ fullPage = false }) {
  const spinner = (
    <div style={{
      width: 36,
      height: 36,
      border: "3px solid #E8ECF0",
      borderTop: "3px solid #E24B4A",
      borderRadius: "50%",
      animation: "spin 0.8s linear infinite",
    }} />
  );

  if (fullPage) {
    return (
      <div style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        {spinner}
      </div>
    );
  }

  return (
    <>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      {spinner}
    </>
  );
}
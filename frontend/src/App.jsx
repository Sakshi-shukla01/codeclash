import { Navigate, Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import AuthPage from "./pages/AuthPage.jsx";
import Battle from "./pages/Battle.jsx";
import Lobby from "./pages/Lobby.jsx";
import Practice from "./pages/Practice.jsx";
import { useSession } from "./session.jsx";

export default function App() {
  const { user, loading } = useSession();

  if (loading) return <div className="center muted">Loading…</div>;
  if (!user) return <AuthPage />;

  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<Lobby />} />
        <Route path="/battle/:id" element={<Battle />} />
        <Route path="/practice/:slug" element={<Practice />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </>
  );
}

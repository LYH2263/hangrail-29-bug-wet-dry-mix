import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import StoresPage from "./pages/StoresPage";
import RailsPage from "./pages/RailsPage";
import OrdersPage from "./pages/OrdersPage";
import OccupancyPage from "./pages/OccupancyPage";
import PickupPage from "./pages/PickupPage";
import OverduePage from "./pages/OverduePage";
export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Navigate to="/occupancy" replace />} />
        <Route path="/stores" element={<StoresPage />} />
        <Route path="/rails" element={<RailsPage />} />
        <Route path="/orders" element={<OrdersPage />} />
        <Route path="/occupancy" element={<OccupancyPage />} />
        <Route path="/pickup" element={<PickupPage />} />
        <Route path="/overdue" element={<OverduePage />} />
      </Route>
    </Routes>
  );
}

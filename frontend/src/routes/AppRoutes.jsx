import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "../layouts/AppLayout";
import BackofficeLayout from "../layouts/BackofficeLayout";
import { useAuth } from "../hooks/useAuth";
import LoginPage from "../pages/LoginPage";
import RegisterPage from "../pages/RegisterPage";
import ProfilePage from "../pages/ProfilePage";
import HomePage from "../pages/HomePage";
import SearchPage from "../pages/SearchPage";
import RestaurantDetailPage from "../pages/RestaurantDetailPage";
import BookingPage from "../pages/BookingPage";
import BookingHistoryPage from "../pages/BookingHistoryPage";
import ReviewPage from "../pages/ReviewPage";
import FavoritesPage from "../pages/FavoritesPage";
import AiRecommendationPage from "../pages/AiRecommendationPage";
import OwnerDashboardPage from "../pages/owner/OwnerDashboardPage";
import OwnerRestaurantsPage from "../pages/owner/OwnerRestaurantsPage";
import OwnerMenuPage from "../pages/owner/OwnerMenuPage";
import OwnerBookingsPage from "../pages/owner/OwnerBookingsPage";
import OwnerReviewsPage from "../pages/owner/OwnerReviewsPage";
import AdminDashboardPage from "../pages/admin/AdminDashboardPage";
import AdminUsersPage from "../pages/admin/AdminUsersPage";
import AdminRestaurantsPage from "../pages/admin/AdminRestaurantsPage";
import AdminAnalyticsPage from "../pages/admin/AdminAnalyticsPage";
import NotFoundPage from "../pages/NotFoundPage";

function ProtectedRoute({ children, roles }) {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated) return <Navigate to="/dang-nhap" replace />;
  if (roles?.length && !roles.includes(user?.role)) return <Navigate to="/" replace />;
  return children;
}

const withLayout = (element) => <AppLayout>{element}</AppLayout>;
const withBackofficeLayout = (role, element) => <BackofficeLayout role={role}>{element}</BackofficeLayout>;

function AppRoutes() {
  return (
    <Routes>
      <Route path="/dang-nhap" element={<LoginPage />} />
      <Route path="/dang-ky" element={<RegisterPage />} />
      <Route path="/" element={withLayout(<HomePage />)} />
      <Route path="/tim-kiem" element={withLayout(<SearchPage />)} />
      <Route path="/nha-hang/:id" element={withLayout(<RestaurantDetailPage />)} />
      <Route path="/dat-ban" element={withLayout(<BookingPage />)} />
      <Route
        path="/lich-su-dat-ban"
        element={withLayout(
          <ProtectedRoute>
            <BookingHistoryPage />
          </ProtectedRoute>
        )}
      />
      <Route path="/danh-gia" element={withLayout(<ReviewPage />)} />
      <Route path="/yeu-thich" element={withLayout(<FavoritesPage />)} />
      <Route path="/ai-goi-y" element={withLayout(<AiRecommendationPage />)} />
      <Route
        path="/ho-so"
        element={withLayout(
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/chu-nha-hang/dashboard"
        element={withBackofficeLayout(
          "owner",
          <ProtectedRoute roles={["owner"]}>
            <OwnerDashboardPage />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/chu-nha-hang/nha-hang"
        element={withBackofficeLayout(
          "owner",
          <ProtectedRoute roles={["owner"]}>
            <OwnerRestaurantsPage />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/chu-nha-hang/menu"
        element={withBackofficeLayout(
          "owner",
          <ProtectedRoute roles={["owner"]}>
            <OwnerMenuPage />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/chu-nha-hang/dat-ban"
        element={withBackofficeLayout(
          "owner",
          <ProtectedRoute roles={["owner"]}>
            <OwnerBookingsPage />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/chu-nha-hang/danh-gia"
        element={withBackofficeLayout(
          "owner",
          <ProtectedRoute roles={["owner"]}>
            <OwnerReviewsPage />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/admin/dashboard"
        element={withBackofficeLayout(
          "admin",
          <ProtectedRoute roles={["admin"]}>
            <AdminDashboardPage />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/admin/phan-tich"
        element={withBackofficeLayout(
          "admin",
          <ProtectedRoute roles={["admin"]}>
            <AdminAnalyticsPage />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/admin/nguoi-dung"
        element={withBackofficeLayout(
          "admin",
          <ProtectedRoute roles={["admin"]}>
            <AdminUsersPage />
          </ProtectedRoute>
        )}
      />
      <Route
        path="/admin/nha-hang"
        element={withBackofficeLayout(
          "admin",
          <ProtectedRoute roles={["admin"]}>
            <AdminRestaurantsPage />
          </ProtectedRoute>
        )}
      />
      <Route path="*" element={withLayout(<NotFoundPage />)} />
    </Routes>
  );
}

export default AppRoutes;

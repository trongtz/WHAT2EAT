import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import AppLayout from "../layouts/AppLayout";
import BackofficeLayout from "../layouts/BackofficeLayout";
import AiRecommendationPage from "../pages/AiRecommendationPage";
import BookingHistoryPage from "../pages/BookingHistoryPage";
import BookingPage from "../pages/BookingPage";
import FavoritesPage from "../pages/FavoritesPage";
import HomePage from "../pages/HomePage";
import LoginPage from "../pages/LoginPage";
import NotFoundPage from "../pages/NotFoundPage";
import ProfilePage from "../pages/ProfilePage";
import RegisterPage from "../pages/RegisterPage";
import RestaurantDetailPage from "../pages/RestaurantDetailPage";
import ReviewPage from "../pages/ReviewPage";
import SearchPage from "../pages/SearchPage";
import AdminAnalyticsPage from "../pages/admin/AdminAnalyticsPage";
import AdminDashboardPage from "../pages/admin/AdminDashboardPage";
import AdminRestaurantsPage from "../pages/admin/AdminRestaurantsPage";
import AdminUsersPage from "../pages/admin/AdminUsersPage";
import OwnerBookingsPage from "../pages/owner/OwnerBookingsPage";
import OwnerDashboardPage from "../pages/owner/OwnerDashboardPage";
import OwnerMenuPage from "../pages/owner/OwnerMenuPage";
import OwnerRestaurantsPage from "../pages/owner/OwnerRestaurantsPage";
import OwnerReviewsPage from "../pages/owner/OwnerReviewsPage";

const getDefaultRouteByRole = (role) => {
  if (role === "owner") return "/chu-nha-hang/dashboard";
  if (role === "admin") return "/admin/dashboard";
  return "/";
};

function ProtectedRoute({ children, roles }) {
  const { isAuthenticated, user } = useAuth();

  if (!isAuthenticated) return <Navigate to="/dang-nhap" replace />;
  if (roles?.length && !roles.includes(user?.role)) {
    return <Navigate to={getDefaultRouteByRole(user?.role)} replace />;
  }

  return children;
}

function CustomerFacingRoute({ children }) {
  const { user } = useAuth();

  if (user?.role === "owner" || user?.role === "admin") {
    return <Navigate to={getDefaultRouteByRole(user.role)} replace />;
  }

  return children;
}

function AuthRoute({ children }) {
  const { isAuthenticated, user } = useAuth();

  if (isAuthenticated) {
    return <Navigate to={getDefaultRouteByRole(user?.role)} replace />;
  }

  return children;
}

const withLayout = (element) => (
  <CustomerFacingRoute>
    <AppLayout>{element}</AppLayout>
  </CustomerFacingRoute>
);

const withBackofficeLayout = (role, element) => <BackofficeLayout role={role}>{element}</BackofficeLayout>;

function AppRoutes() {
  return (
    <Routes>
      <Route
        path="/dang-nhap"
        element={
          <AuthRoute>
            <LoginPage />
          </AuthRoute>
        }
      />
      <Route
        path="/dang-ky"
        element={
          <AuthRoute>
            <RegisterPage />
          </AuthRoute>
        }
      />
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

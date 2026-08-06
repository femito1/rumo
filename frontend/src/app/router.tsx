// frontend/src/app/router.tsx
import { createBrowserRouter } from "react-router-dom";
import { RequireAuth, RequireAdmin, RequireUserManager, HomeRedirect } from "./guards";
import { LoginPage } from "../features/auth/LoginPage";
import { ChangePasswordPage } from "../features/auth/ChangePasswordPage";
import { ClientsPage } from "../features/clients/ClientsPage";
import { WorkspacePage } from "../features/closing/WorkspacePage";
import { UsuariosPage } from "../features/users/UsuariosPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: <RequireAuth />,
    children: [
      { element: <RequireAdmin />, children: [{ path: "/clientes", element: <ClientsPage /> }] },
      // ADMIN *or* CLIENT_ADMIN: a Gestor manages its own client's logins, and is
      // scoped to it server-side. Not under RequireAdmin, which guards the
      // cross-tenant surfaces.
      { element: <RequireUserManager />, children: [{ path: "/usuarios", element: <UsuariosPage /> }] },
      { path: "/clientes/:id", element: <WorkspacePage /> },
      { path: "/trocar-senha", element: <ChangePasswordPage /> },
      { path: "/", element: <HomeRedirect /> },
    ],
  },
]);

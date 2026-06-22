// frontend/src/app/router.tsx
import { createBrowserRouter } from "react-router-dom";
import { RequireAuth, RequireAdmin } from "./guards";
import { LoginPage } from "../features/auth/LoginPage";
import { ClientsPage } from "../features/clients/ClientsPage";
import { WorkspacePage } from "../features/closing/WorkspacePage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: <RequireAuth />,
    children: [
      { element: <RequireAdmin />, children: [{ path: "/clientes", element: <ClientsPage /> }] },
      { path: "/clientes/:id", element: <WorkspacePage /> },
      { path: "/", element: <ClientsPage /> },
    ],
  },
]);

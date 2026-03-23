import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { StudentApp } from "./student/StudentApp";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <StudentApp />
  </StrictMode>
);

/**
 * CareerKit AI - Client-side Utilities
 * Handles mobile sidebar toggling, alert dismissal, confirmation dialogs,
 * text counters, and safe CSRF submission helpers.
 */

document.addEventListener("DOMContentLoaded", () => {
  // 1. Mobile Sidebar Navigation Toggle
  const sidebar = document.getElementById("sidebar");
  const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");

  if (sidebarToggleBtn && sidebar) {
    sidebarToggleBtn.addEventListener("click", () => {
      sidebar.classList.toggle("open");
    });

    // Close sidebar on click outside on mobile
    document.addEventListener("click", (e) => {
      if (
        window.innerWidth <= 900 &&
        sidebar.classList.contains("open") &&
        !sidebar.contains(e.target) &&
        !sidebarToggleBtn.contains(e.target)
      ) {
        sidebar.classList.remove("open");
      }
    });
  }

  // 2. Dismissible Alerts
  const alertCloseButtons = document.querySelectorAll(".alert-close");
  alertCloseButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const alert = btn.closest(".alert");
      if (alert) {
        alert.style.transition = "opacity 0.2s ease, transform 0.2s ease";
        alert.style.opacity = "0";
        alert.style.transform = "translateY(-6px)";
        setTimeout(() => alert.remove(), 200);
      }
    });
  });

  // 3. Confirmation Dialogs for Destructive Actions
  const confirmActions = document.querySelectorAll("[data-confirm]");
  confirmActions.forEach((element) => {
    element.addEventListener("click", (e) => {
      const message =
        element.getAttribute("data-confirm") ||
        "Are you sure you want to proceed with this action?";
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });

  // 4. Live Word & Character Counter
  const countInputs = document.querySelectorAll("[data-word-count-target]");
  countInputs.forEach((input) => {
    const targetId = input.getAttribute("data-word-count-target");
    const targetEl = document.getElementById(targetId);

    if (targetEl) {
      const updateCount = () => {
        const text = input.value.trim();
        const words = text ? text.split(/\s+/).length : 0;
        const chars = input.value.length;
        targetEl.textContent = `${words} words (${chars} characters)`;
      };
      input.addEventListener("input", updateCount);
      updateCount();
    }
  });
});

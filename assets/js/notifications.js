function initNotifications() {
  const notificationHint = document.getElementById("notification-hint");
  const requestButton = document.getElementById("notification-request");

  if (Notification.permission == "default") {
    notificationHint.classList.remove("hidden");
  }

  requestButton.addEventListener("click", (e) => {
    Notification.requestPermission((permission) => {
      if (permission != "default") {
        notificationHint.classList.add("hidden");
      }
    });
  });
}

if (document.readyState != "loading") {
  initNotifications();
} else {
  document.addEventListener("DOMContentLoaded", () => initNotifications());
}

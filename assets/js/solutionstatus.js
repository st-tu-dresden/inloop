$(document).ready(function() {
  $(".timeago").timeago();
  $(".solution-pending").refreshJSON("activate", {
    url: "/solutions/:id:/status",
    interval: 5000,
    success: function(data) {
      $(this).attr("class", "glyphicon solution-" + data.status);
      if (data.status != "pending") {
        $(this).refreshJSON("deactivate");
      }
    }
  });
});

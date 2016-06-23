$(document).ready(function() {
  anchors.add(".autolink h2, .autolink h3");

  $(".solution-pending").refreshJSON("activate", {
    url: "/tasks/solution/:id:/status",
    interval: 5000,
    success: function(data) {
      $(this).attr("class", "glyphicon solution-" + data.status);
      if (data.status != "pending") {
        $(this).refreshJSON("deactivate");
      }
    }
  });
});

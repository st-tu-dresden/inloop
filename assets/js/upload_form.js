function displayText(files) {
  if (files.length > 1) {
    return files.length + " files selected";
  } else if (files.length == 1) {
    return files[0].name;
  }
  return "";
}

document.getElementById("uploadBtn").addEventListener("change", function () {
  document.getElementById("submit").submit();
});



function displayText(files) {
  if (files.length > 1) {
    return files.length + " files selected";
  } else if (files.length == 1) {
    return files[0].name;
  }
  return "";
}

document.getElementById("submit-button").style.display = "none";

document.getElementById("file-input").addEventListener("change", function () {
  document.getElementById("file-upload-form").submit();
});



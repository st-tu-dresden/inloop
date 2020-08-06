export const msgs = {
  try_again_later: 'Please try again later.',
  upload_failed: 'Upload failed.',
  duplicate_filename: 'A file with the name "%filename%" already exists.\nPlease choose another filename.',
  invalid_filename: '"%filename%" is not a valid Java filename.\nMake sure to add the correct file suffix (.java).',
  choose_filename: 'Please enter a name for your new file.',
  edit_filename: 'Renaming "%filename%".\nPlease enter a new file name.',
  delete_file_confirmation: 'Are you sure you want to delete "%filename%"?',
  missing_es6_support: 'Your browser does not support ECMAScript 6. Please update or change your browser to use the editor.',
  error_loading_files: 'Error occured: Could not load saved files from server.'
};

export function getString(string, extra) {
  if (extra) {
    return string.replace(/\%.*\%/, extra);
  } else {
    return string;
  }
  
}
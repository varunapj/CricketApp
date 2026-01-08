document.addEventListener('DOMContentLoaded', function () {
  const masterUpload = document.getElementById('upload-master');
  const masterFile = document.querySelector('input[name="master_file"]');

  const availUpload = document.getElementById('upload-avail');
  const availFile = document.querySelector('input[name="availability_file"]');

  function updateMaster() {
    // file input display is handled by CSS; keep JS to prevent submission without file
  }
  function updateAvail() {
    // no-op: CSS handles visibility
  }

  if (masterUpload) masterUpload.addEventListener('change', updateMaster);
  if (availUpload) availUpload.addEventListener('change', updateAvail);

  updateMaster();
  updateAvail();

  // basic validation on submit
  const form = document.getElementById('splitForm');
  if (form) {
    form.addEventListener('submit', function (e) {
      // ensure master chosen (repo is default)
      const masterUploadChecked = document.getElementById('upload-master') && document.getElementById('upload-master').checked;
      if (masterUploadChecked && masterFile && masterFile.files.length === 0) {
        e.preventDefault();
        alert('You selected to upload a master file but did not choose a file.');
        return false;
      }

      const availUploadChecked = document.getElementById('upload-avail') && document.getElementById('upload-avail').checked;
      if (availUploadChecked && availFile && availFile.files.length === 0) {
        e.preventDefault();
        alert('You selected to upload an availability file but did not choose a file.');
        return false;
      }

      // optional: validate extensions
      function extOk(file) {
        if (!file) return true;
        const allowed = ['.tsv','.txt','.csv','.xlsx','.xls'];
        const name = file.name.toLowerCase();
        return allowed.some(ext => name.endsWith(ext));
      }
      if (masterUploadChecked && masterFile && masterFile.files.length > 0 && !extOk(masterFile.files[0])) {
        e.preventDefault();
        alert('Unsupported master file type. Allowed: TSV, CSV, XLSX, XLS.');
        return false;
      }
      if (availUploadChecked && availFile && availFile.files.length > 0 && !extOk(availFile.files[0])) {
        e.preventDefault();
        alert('Unsupported availability file type. Allowed: TSV, CSV, XLSX, XLS.');
        return false;
      }
    });
  }
});

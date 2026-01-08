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
        alert('You selected to upload a master TSV but did not choose a file.');
        return false;
      }

      const availUploadChecked = document.getElementById('upload-avail') && document.getElementById('upload-avail').checked;
      if (availUploadChecked && availFile && availFile.files.length === 0) {
        e.preventDefault();
        alert('You selected to upload availability but did not choose a file.');
        return false;
      }
    });
  }
});

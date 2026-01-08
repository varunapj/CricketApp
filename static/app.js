document.addEventListener('DOMContentLoaded', function () {
  const masterRepo = document.getElementById('master_repo');
  const masterUpload = document.getElementById('master_upload');
  const masterFile = document.getElementById('master_file');

  const availNone = document.getElementById('avail_none');
  const availUpload = document.getElementById('avail_upload');
  const availFile = document.getElementById('availability_file');

  function updateMaster() {
    masterFile.disabled = masterRepo.checked;
  }
  function updateAvail() {
    availFile.disabled = !(availUpload && availUpload.checked);
  }

  [masterRepo, masterUpload].forEach(el => el && el.addEventListener('change', updateMaster));
  [availNone, availUpload].forEach(el => el && el.addEventListener('change', updateAvail));

  updateMaster();
  updateAvail();

  // basic validation on submit
  const form = document.getElementById('splitForm');
  if (form) {
    form.addEventListener('submit', function (e) {
      // ensure master chosen (repo is default)
      if (masterUpload && masterUpload.checked && masterFile && masterFile.files.length === 0) {
        e.preventDefault();
        alert('You selected to upload a master TSV but did not choose a file.');
        return false;
      }

      if (availUpload && availUpload.checked && availFile && availFile.files.length === 0) {
        e.preventDefault();
        alert('You selected to upload availability but did not choose a file.');
        return false;
      }
    });
  }
});

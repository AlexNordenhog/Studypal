// Firebase configuration and initialization
import firebaseConfig from "{{ url_for('static', filename='firebase-cfg.js') }}";
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js";
import {
    getStorage,
    ref,
    uploadBytesResumable,
    getDownloadURL,
} from "https://www.gstatic.com/firebasejs/10.8.1/firebase-storage.js";
import { app, auth, userExists } from "../static/index.js";

// Add event listener to submit button
document.getElementById("submitUploadBtn").addEventListener("click", () => {
    uploadDocument();
});

function uploadDocument() {
    var fileInput = document.getElementById("pdf_file");
    var file = fileInput.files[0];

    // Create a storage reference
    var storage = getStorage(app);
    var storageRef = ref(storage, "temp/" + file.name);

    // Upload file to Firebase Storage
    var uploadTask = uploadBytesResumable(storageRef, file);

    // Listen for state changes, errors, and completion of the upload.
    uploadTask.on(
    "state_changed",
    function (snapshot) {
        // Handle upload progress
        var progress =
        (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
        console.log("Upload is " + progress + "% done");
    },
    function (error) {
        // Handle unsuccessful upload
        console.error("Error uploading file:", error);
    },
    function () {
        // Handle successful upload
        getDownloadURL(uploadTask.snapshot.ref).then(function (downloadURL) {
        console.log("File available at", downloadURL);
        // Once you have the downloadURL, you can add it to the form data and submit the form
        var formData = new FormData(document.getElementById("uploadForm"));
        formData.append("downloadURL", downloadURL); // Add downloadURL to form data

        // Now you can submit the form with all data, including the downloadURL
        submitForm(formData);
        });
    }
    );
}

function submitForm(formData) {
    // Submit the form with all data, including the downloadURL
    fetch("/upload_document", {
    method: "POST",
    body: formData,
    })
    .then((response) => {
        if (!response.ok) {
        throw new Error("Network response was not ok");
        }
        return response.text();
    })
    .then((data) => {
        console.log(data); // Handle success response
    })
    .catch((error) => {
        console.error("There was a problem with the fetch operation:", error);
    });
}
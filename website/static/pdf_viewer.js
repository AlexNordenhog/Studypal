// Initialize Firebase in your app
// Ensure you have included Firebase SDK and initialized your Firebase app

// Reference to your Firebase storage and the PDF file
var storageRef = firebase.storage().ref('path/to/your/pdf/file.pdf');

// Get the PDF file as a Blob
storageRef.getBlob().then(function(blob) {
  // Use PDF.js to render the PDF
  var url = URL.createObjectURL(blob);
  var pdfjsLib = window['pdfjs-dist/build/pdf'];

  // The workerSrc property shall be specified.
  pdfjsLib.GlobalWorkerOptions.workerSrc = '//mozilla.github.io/pdf.js/build/pdf.worker.js';

  // Asynchronous download of PDF
  var loadingTask = pdfjsLib.getDocument(url);
  loadingTask.promise.then(function(pdf) {
    console.log('PDF loaded');
    
    // Fetch the first page
    var pageNumber = 1;
    pdf.getPage(pageNumber).then(function(page) {
      console.log('Page loaded');
      
      var scale = 1.5;
      var viewport = page.getViewport({scale: scale});

      // Prepare canvas using PDF page dimensions
      var canvas = document.getElementById('pdf-canvas');
      var context = canvas.getContext('2d');
      canvas.height = viewport.height;
      canvas.width = viewport.width;

      // Render PDF page into canvas context
      var renderContext = {
        canvasContext: context,
        viewport: viewport
      };
      var renderTask = page.render(renderContext);
      renderTask.promise.then(function () {
        console.log('Page rendered');
      });
    });
  }, function (reason) {
    // PDF loading error
    console.error(reason);
  });
});


// If we want to implement hidden doc from beginning maybe to increase performance?
// document.getElementById('togglePdfViewer').addEventListener('click', function() {
//     var pdfViewer = document.getElementById('pdfViewer');
//     pdfViewer.style.display = pdfViewer.style.display === 'none' ? 'block' : 'none';
// });



// Added to test the comment UI
// We will have to implement comments linked with firebase later  
document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("submitComment")
    .addEventListener("click", function () {
      const commentInput = document.getElementById("commentInput");
      const commentText = commentInput.value.trim();

      if (commentText) {
        // Create the comment element
        const comment = document.createElement("div");
        comment.classList.add("comment");

        comment.innerHTML = `
          <div class="comment-avatar">
              <p>profilbild</p>
          </div>
          <div class="comment-content">
              <div class="comment-author">Testnamn</div>
              <div class="comment-text">${commentText}</div>
          </div>
      `;

        // Append the new comment to the comments display area
        document.querySelector(".comments-display").appendChild(comment);

        // Clear the input field
        commentInput.value = "";
      }
    });
});



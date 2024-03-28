// Firebase configuration and initialization
import firebaseConfig from "{{ url_for('static', filename='firebase-cfg.js') }}";
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js";
import {
getAuth,
onAuthStateChanged,
} from "https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js";
import {
getDatabase,
ref,
child,
get,
set,
} from "https://www.gstatic.com/firebasejs/10.8.1/firebase-database.js";

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const document_id = "{{document_dict['id']}}";

// Function to check if user exists in the database
function userExists(uid) {
const dbRef = ref(getDatabase());
return get(child(dbRef, `Users/${uid}`))
    .then((snapshot) => {
    return snapshot.exists();
    })
    .catch((error) => {
    console.error(error);
    return false;
    });
}

function fetchUser(uid) {
const url = "/get_user"; // Update this URL to match your Flask endpoint

const data = {
    uid: uid,
};

return fetch(url, {
    method: "POST",
    headers: {
    "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
})
    .then((response) => response.json())
    .catch((error) => {
    console.error(error);
    return null;
    });
}

// Check if user is signed in and get user's UID
onAuthStateChanged(auth, (user) => {
if (user) {
    const uid = user.uid;
    console.log("User is signed in with UID:", uid);

    // Call your function here with UID if needed
    document.getElementById("likeBtn").addEventListener("click", function () {
    castVote(true, uid);
    });

    document
    .getElementById("dislikeBtn")
    .addEventListener("click", function () {
        castVote(false, uid);
    });
} else {
    console.log("User is signed out");
    // Redirect user to sign in page or handle the case where user is not signed in
}
});

function validateDocument(documentId) {
fetch(`/validate_document/${documentId}`, {
    method: "POST",
    headers: {
    "Content-Type": "application/json",
    },
    body: JSON.stringify({}),
})
    .then((response) => {
    if (response.ok) {
        return response.text();
    } else {
        throw new Error("Network response was not ok.");
    }
    })
    .then((data) => {
    console.log(data);
    //success
    })
    .catch((error) => {
    console.error(
        "There has been a problem with your fetch operation:",
        error
    );
    });
}

function castVote(isUpvote, uid) {
var documentId = "{{ document_dict['id'] }}";
if (!documentId) {
    alert("Document ID not available!");
    return;
}
fetch("/vote_document", {
    method: "POST",
    body: JSON.stringify({
    uid: uid,
    document_id: documentId,
    is_upvote: isUpvote,
    }),
    headers: {
    "Content-Type": "application/json",
    },
})
    .then((response) => response.json())
    .then((data) => {
    console.log("Successfully added vote");
    })
    .catch((error) => {
    console.error("Error:", error);
    });
}

// <!-- Dynamic commentsection -->
document
.getElementById("submitComment")
.addEventListener("click", function () {
    const commentInput = document.getElementById("commentInput");
    const commentText = commentInput.value.trim();
    const db = getDatabase();
    const auth = getAuth();

    if (commentText && auth.currentUser) {
    fetch("/add_document_comment", {
        method: "POST",
        body: JSON.stringify({
        uid: auth.currentUser.uid,
        document_id: "{{ document_dict['id'] }}",
        text: commentText,
        }),
        headers: {
        "Content-Type": "application/json",
        },
    })
        .then((response) => response.json())
        .then((data) => {
        console.log(data.message);
        window.location.reload();
        commentInput.value = "";
        })
        .catch((error) => {
        console.error("Error:", error);
        });
    } else {
    console.log("User is not signed in or comment is empty.");
    }
});

// Report extraction
document
.getElementById("submitReport")
.addEventListener("click", function () {
    const reportReasonSelect = document.getElementById("reportReason");
    const reportReason = reportReasonSelect.value;
    const reportText = document.getElementById("reportText").value;

    // Assuming the user is already signed in and you have their UID
    const uid = auth.currentUser ? auth.currentUser.uid : null;
    const documentId = "{{ document_dict['id'] }}";

    if (!uid) {
    alert("You must be signed in to submit a report.");
    return;
    }

    const reportData = {
    uid: uid,
    document_id: documentId,
    reason: reportReason,
    text: reportText,
    };

    fetch("/add_document_report", {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
    },
    body: JSON.stringify(reportData),
    })
    .then((response) => response.json())
    .then((data) => {
        console.log(data.message);
        $("#reportModal").modal("hide");
        reportReasonSelect.value = reportReasonSelect.options[0].value;
        document.getElementById("reportText").value = "";
    })
    .catch((error) => {
        console.error("Error:", error);
    });
});

// Check if the user is signed in and a moderator
onAuthStateChanged(auth, (user) => {
if (user) {
    // Fetch user details to check if the user is a moderator
    fetchUser(user.uid).then((userData) => {
    if (userData && userData.role === "moderator") {
        console.log("User is a moderator.");

        // Make a button beside the like counter if user is a moderator
        const moderatorMenuBtn = document.createElement("button");
        moderatorMenuBtn.className = "btn btn-primary";
        moderatorMenuBtn.type = "button";
        moderatorMenuBtn.innerText = "Mod Menu";
        moderatorMenuBtn.setAttribute("data-toggle", "modal");
        moderatorMenuBtn.setAttribute("data-target", "#modMenuModal");

        const buttonBar = document.querySelector(".button-bar");

        if (buttonBar) {
        buttonBar.appendChild(moderatorMenuBtn);
        } else {
        console.error("Button bar not found");
        }
    } else {
        console.log("User is not a moderator.");
    }
    });
} else {
    console.log("User is not signed in.");
    // Handle not signed-in state
    window.location.href = "/login";
}
});

document.addEventListener("DOMContentLoaded", function () {
// Event listener for when the Mod Menu Modal is fully shown
$("#modMenuModal").on("shown.bs.modal", function (event) {
    const deleteButton = document.getElementById("deleteDocument");
    deleteButton.onclick = function () {
    const documentId = '{{ document_dict["id"] }}';
    deleteDocument(documentId);
    };
});
});

function deleteDocument(document_id) {
fetch(`/validate_document/${document_id}`, {
    method: "POST",
    headers: {
    "Content-Type": "application/json",
    },
    body: JSON.stringify({ approve: false }),
})
    .then((response) => {
    if (response.ok) {
        alert("Document was successfully removed.");
        window.location.href = "/";
    } else {
        throw new Error("Failed to delete the document.");
    }
    })
    .catch((error) => {
    console.error("Error:", error);
    alert("An error occurred while trying to delete the document.");
    });
}


// Gamla like/dislike functionen
// function vote(action, documentId) {
//     const form = new FormData();
//     form.append("action", action);
//     form.append("document_id", documentId);
  
//     fetch(`/vote/${action}/${documentId}`, {
//       method: "POST",
//       body: form,
//     }).then((response) => {
//       // Reload the page after the fetch completes
//       window.location.reload();
//     });
//   }


// Allt nedan kommer behöva kopplas till riktig data från databasen
// Define variables
const hand_button = document.getElementById("likeBtn")
const hand_button_dislike = document.getElementById("dislikeBtn")
const thumb_up_icon = document.getElementById("thumbUpIcon")
const thumb_down_icon = document.getElementById("thumbDownIcon")
// const total_likes = document.getElementById("totalLikes")

// Liking function
function add_like() {
    hand_button.setAttribute("class", "heartbeat greenHand")
    hand_button_dislike.setAttribute("class", "heartbeat redHand")
    thumb_up_icon.setAttribute("class", "bi bi-hand-thumbs-up-fill")
    // thumb_up_icon.setAttribute("id", "liked")
    thumb_down_icon.setAttribute("class", "bi bi-hand-thumbs-down-fill")
    // thumb_up_icon.setAttribute("id", "liked")
    // total_likes.innerHTML = parseInt(total_likes.innerHTML) + 1
}

// Unliking function
function remove_like() {
    hand_button.setAttribute("class", "blackHand")
    hand_button_dislike.setAttribute("class", "blackHand")
    thumb_up_icon.setAttribute("class", "bi bi-hand-thumbs-up")
    // thumb_up_icon.setAttribute("id", "not-liked")
    thumb_down_icon.setAttribute("class", "bi bi-hand-thumbs-down")
    // thumb_up_icon.setAttribute("id", "not-liked")
    // total_likes.innerHTML = parseInt(total_likes.innerHTML) - 1
}

// Remove heartbeat animation
function remove_heartbeat() {
    hand_button.setAttribute("class", "greenHand")
    hand_button_dislike.setAttribute("class", "redHand")
}

// When like button clicked
hand_button.onclick = function () {
    const like_checker = document.getElementById("liked")
    if (like_checker == null) {
        add_like()
        setTimeout(remove_heartbeat, 1000)
    } else {
        remove_like()
    }
}

// When dislike button clicked
hand_button_dislike.onclick = function () {
    const like_checker = document.getElementById("liked")
    if (like_checker == null) {
        add_like()
        setTimeout(remove_heartbeat, 1000)
    } else {
        remove_like()
    }
}




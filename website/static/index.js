import { initializeApp } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-app.js";
import { GoogleAuthProvider, getAuth, signInWithPopup, onAuthStateChanged } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-auth.js";
import { getDatabase, ref, set, get, child } from "https://www.gstatic.com/firebasejs/10.8.1/firebase-database.js";
import firebaseConfig from "./firebase-cfg.js";

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();
const db = getDatabase();

function userExists(uid) {
    const url = "/get_user";

    const data = {
        uid: uid
    };

    return fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(data => {
            // check if the username is not equal to this value.
            if (data.username && data.username !== "404 unknown user") {
                return true; // User exists
            }
            return false; // User does not exist
        })
        .catch(error => {
            console.error(error);
            return false; // Assume user does not exist if there's an error
        });
}





// Export the function to get the UID

export { app, auth, provider, db, userExists }
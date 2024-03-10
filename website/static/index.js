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
            if ("username" in data) {
                return data.username !== "unregistered user";
            }
            return false;
        })
        .catch(error => {
            console.error(error);
            return false;
        });
}




// Export the function to get the UID

export { app, auth, provider, db, userExists }
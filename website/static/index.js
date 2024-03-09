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
    const dbRef = ref(getDatabase());

    return get(child(dbRef, "Users/"))
        .then((snapshot) => {
            let userExists = false;
            snapshot.forEach((childSnapshot) => {
                const current_uid = childSnapshot.key;
                if (uid === current_uid) {
                    userExists = true;
                    return true;
                }
            });
            return userExists;
        })
        .catch((error) => {
            console.error(error);
            return false;
        });
}



// Export the function to get the UID

export { app, auth, provider, db, userExists }
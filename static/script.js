// const users = [
//     // Temporary storage for user data (Replace with a database or API in a real app)
//     { regNo: "12345", phone: "1234567890", email: "user1@example.com", address: "123 Street, City" },
//     { regNo: "67890", phone: "0987654321", email: "user2@example.com", address: "456 Avenue, City" }
// ];

// Function to search for a user's contact details by registration number
// function searchContact() {
//     let regNoInput = document.getElementById("reg_number"); // Get the input field for registration number
//     let reg_number = regNoInput.value.trim(); // Trim any leading or trailing whitespace
//     let user = users.find(user => user.reg_number === reg_number); // Search for a user with the entered registration number

//     if (user) {
//         alert(`User found! Phone: ${user.phone}`); // Alert with the user's phone number if found
//         regNoInput.style.border = "2px solid green"; // Change input border to green to indicate success
//     } else {
//         alert("User not found!"); // Alert if the user is not found
//         regNoInput.style.border = "2px solid red"; // Change input border to red to indicate failure
//     }
// }

// Add an event listener to handle form submission
// Prevents default form submission and calls searchContact instead

// document.getElementById("forgotPassword").addEventListener("submit", function(event) {
//     event.preventDefault(); // Prevent the form from actually submitting
//     searchContact(); // Call the function to search for the user
// });

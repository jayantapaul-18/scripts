// JavaScript for Task and Note Tracker
document.addEventListener('DOMContentLoaded', () => {
    // Select DOM elements
    const taskInput = document.getElementById('new-task');
    const taskList = document.getElementById('task-list');
    const addTaskButton = document.getElementById('add-task');

    const noteInput = document.getElementById('new-note');
    const noteList = document.getElementById('note-list');
    const addNoteButton = document.getElementById('add-note');

    // Load saved tasks and notes from localStorage
    loadTasks();
    loadNotes();

    // Add new task
    addTaskButton.addEventListener('click', () => {
        const taskText = taskInput.value.trim();
        if (taskText) {
            addTask(taskText);
            saveTaskToLocalStorage(taskText);
            taskInput.value = ''; // Clear input
        }
    });

    // Add new note
    addNoteButton.addEventListener('click', () => {
        const noteText = noteInput.value.trim();
        if (noteText) {
            addNote(noteText);
            saveNoteToLocalStorage(noteText);
            noteInput.value = ''; // Clear input
        }
    });

    // Function to add task to the UI
    function addTask(taskText) {
        const taskItem = document.createElement('li');
        taskItem.classList.add('task-item');
        taskItem.innerHTML = `
            <span>${taskText}</span>
            <button class="delete-task">Delete</button>
        `;
        taskList.appendChild(taskItem);

        // Delete task
        taskItem.querySelector('.delete-task').addEventListener('click', () => {
            taskItem.remove();
            removeTaskFromLocalStorage(taskText);
        });
    }

    // Function to add note to the UI
    function addNote(noteText) {
        const noteItem = document.createElement('li');
        noteItem.classList.add('

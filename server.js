// Existing imports and setup
...
// Command handling
switch (request.command) {
  // existing cases
  case 'bpm':
    // Send current BPM to client (placeholder value)
    socket.emit('bpm', {value: 120});
    break;
  // other cases
}
...
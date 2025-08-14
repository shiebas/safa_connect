# SAFA Connect Invoice System: Voice Command Reference

This document outlines the voice commands implemented in the multimedia training system for the SAFA Connect invoice system.

## Available Voice Commands

### Navigation Commands

| Voice Command | Action |
|---------------|--------|
| "Start training" | Begins the training session |
| "Pause video" | Pauses current video playback |
| "Resume video" | Continues video playback |
| "Next module" | Advances to next training module |
| "Previous module" | Returns to previous module |
| "Show transcript" | Displays video transcript |
| "Hide transcript" | Hides transcript panel |

### Module Selection

| Voice Command | Action |
|---------------|--------|
| "Open module one" | Loads System Introduction module |
| "Open module two" | Loads Registration & Invoice Generation module |
| "Open module three" | Loads Payment Processing module |
| "Open module four" | Loads Invoice Management module |
| "Open module five" | Loads Reporting Capabilities module |
| "Open module six" | Loads Administrator Tools module |

### Language Selection

| Voice Command | Action |
|---------------|--------|
| "Switch to English" | Changes language to English |
| "Switch to isiZulu" | Changes language to isiZulu |
| "Switch to isiXhosa" | Changes language to isiXhosa |
| "Switch to Afrikaans" | Changes language to Afrikaans |
| "Switch to Sesotho" | Changes language to Sesotho |

### Q&A Functionality

| Voice Command | Action |
|---------------|--------|
| "Ask a question" | Activates Q&A mode |
| "How do I register a player?" | Jumps to relevant section in training |
| "What is the fee for junior players?" | Provides answer about junior fees |
| "How do I mark an invoice as paid?" | Shows instructions for payment processing |
| "What are overdue invoices?" | Explains invoice status types |
| "What's the payment reference format?" | Explains payment reference generation |

## Speech Recognition Implementation

```javascript
// Sample implementation of speech recognition functionality
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();

recognition.continuous = true;
recognition.interimResults = false;
recognition.maxAlternatives = 1;
recognition.lang = 'en-ZA';  // Default language

let listening = false;

// Configure language detection
function setRecognitionLanguage(language) {
    switch (language) {
        case 'english':
            recognition.lang = 'en-ZA';
            break;
        case 'isizulu':
            recognition.lang = 'zu-ZA';
            break;
        case 'isixhosa':
            recognition.lang = 'xh-ZA';
            break;
        case 'afrikaans':
            recognition.lang = 'af-ZA';
            break;
        case 'sesotho':
            recognition.lang = 'st-ZA';
            break;
        default:
            recognition.lang = 'en-ZA';
    }
    
    console.log(`Speech recognition language set to: ${recognition.lang}`);
}

// Start/stop voice recognition
function toggleVoiceRecognition() {
    if (!listening) {
        recognition.start();
        listening = true;
        document.getElementById('voice-status').textContent = 'Listening...';
    } else {
        recognition.stop();
        listening = false;
        document.getElementById('voice-status').textContent = 'Voice recognition off';
    }
}

// Process voice commands
recognition.onresult = function(event) {
    const command = event.results[event.results.length - 1][0].transcript.toLowerCase().trim();
    console.log(`Voice command detected: "${command}"`);
    
    // Navigation commands
    if (command.includes('start training')) {
        startTraining();
    } else if (command.includes('pause video')) {
        pauseVideo();
    } else if (command.includes('resume video')) {
        resumeVideo();
    } else if (command.includes('next module')) {
        nextModule();
    } else if (command.includes('previous module')) {
        previousModule();
    } else if (command.includes('show transcript')) {
        showTranscript();
    } else if (command.includes('hide transcript')) {
        hideTranscript();
    }
    
    // Module selection
    else if (command.includes('module one') || command.includes('module 1')) {
        loadModule(1);
    } else if (command.includes('module two') || command.includes('module 2')) {
        loadModule(2);
    } else if (command.includes('module three') || command.includes('module 3')) {
        loadModule(3);
    } else if (command.includes('module four') || command.includes('module 4')) {
        loadModule(4);
    } else if (command.includes('module five') || command.includes('module 5')) {
        loadModule(5);
    } else if (command.includes('module six') || command.includes('module 6')) {
        loadModule(6);
    }
    
    // Language selection
    else if (command.includes('switch to english')) {
        setLanguage('english');
    } else if (command.includes('switch to isizulu')) {
        setLanguage('isizulu');
    } else if (command.includes('switch to isixhosa')) {
        setLanguage('isixhosa');
    } else if (command.includes('switch to afrikaans')) {
        setLanguage('afrikaans');
    } else if (command.includes('switch to sesotho')) {
        setLanguage('sesotho');
    }
    
    // Q&A functionality
    else if (command.includes('how do i register a player')) {
        jumpToSection('player-registration');
    } else if (command.includes('fee for junior') || command.includes('junior fee')) {
        showAnswer('The fee for junior players is R100.00 as defined in the system configuration.');
    } else if (command.includes('mark as paid') || command.includes('mark invoice as paid')) {
        jumpToSection('marking-paid');
    } else if (command.includes('what are overdue')) {
        showAnswer('Overdue invoices are those where the payment due date has passed without payment being received.');
    } else if (command.includes('payment reference')) {
        jumpToSection('payment-references');
    }
    
    // Unknown command
    else {
        showAnswer(`I'm sorry, I didn't understand the command: "${command}"`);
    }
};

recognition.onerror = function(event) {
    console.error(`Speech recognition error: ${event.error}`);
    document.getElementById('voice-status').textContent = `Error: ${event.error}`;
};

recognition.onend = function() {
    // Restart recognition if it was still supposed to be listening
    if (listening) {
        recognition.start();
    }
};
```

## Voice Recognition Testing Protocol

1. **Environment Setup**:
   - Test in a quiet environment
   - Use a high-quality microphone
   - Ensure stable internet connection

2. **Initial Training**:
   - Train the system on South African accents
   - Include both male and female voices
   - Cover all 11 official languages

3. **Testing Procedure**:
   - Test each command 5 times per language
   - Record success rate and false positives
   - Document any consistent misinterpretations

4. **Accuracy Benchmarks**:
   - Navigation commands: minimum 95% accuracy
   - Module selection: minimum 90% accuracy
   - Q&A responses: minimum 85% accuracy

5. **Continuous Learning**:
   - Implement feedback mechanism for failed commands
   - Store misinterpreted phrases for model improvement
   - Update recognition model monthly with new data

## Current Limitations

1. **Background Noise**: Performance degrades in noisy environments
2. **Technical Terminology**: May struggle with technical invoice terms
3. **Mixed Language Commands**: Cannot process commands that mix languages
4. **Accents**: Requires more training data for certain regional accents
5. **Complex Questions**: Limited to predefined Q&A patterns

## Future Enhancements

1. **Expanded Q&A Database**: Add more invoice-specific questions and answers
2. **Contextual Understanding**: Improve ability to understand commands in context
3. **Custom Voice Training**: Allow users to train the system on their own voice
4. **Dialect Support**: Add support for regional dialects within languages
5. **Offline Mode**: Enable basic voice commands without internet connection

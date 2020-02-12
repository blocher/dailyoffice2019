import Artyom from "artyom.js"
const artyom = new Artyom();
const textToSpeech = require('@google-cloud/text-to-speech');
const fs = require('fs');
const util = require('util');
const projectId = 'dailyoffice2019';
const keyFilename = '';

const client = new textToSpeech.TextToSpeechClient({projectId, keyFilename});
  async function quickStart() {

    // The text to synthesize
    const text = 'hello, world!';

    // Construct the request
    const request = {
      input: {text: text},
      // Select the language and SSML voice gender (optional)
      voice: {languageCode: 'en-US', ssmlGender: 'NEUTRAL'},
      // select the type of audio encoding
      audioConfig: {audioEncoding: 'MP3'},
    };

    // Performs the text-to-speech request
    const [response] = await client.synthesizeSpeech(request);
    // Write the binary audio content to a local file
    const writeFile = util.promisify(fs.writeFile);
    await writeFile('output.mp3', response.audioContent, 'binary');
    console.log('Audio content written to file: output.mp3');
  }


function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

const getVoices = async () => {

    let synth = window.speechSynthesis;

    let voices = null;

    while (true == true) {
        await sleep(100);
        if (synth.getVoices().length !== 0) {
            voices = synth.getVoices().filter((voice) => {
                return voice.lang == 'en' || voice.lang.includes("en-");
            });
            break;
        }
    }
    console.log(voices);
    if (voices.filter((voice) => {
        return voice.name == "Google US English";
    }).length) {
        return {
            "officiant": voices.filter((voice) => {
                return voice.name == "Google UK English Male";
            })[0],
            "respondent": voices.filter((voice) => {
                return voice.name == "Google US English";
            })[0]
        };
    }

    if (voices.filter((voice) => {
        return voice.name == "Microsoft Jessa Online (Natural) - English (United States)";
    }).length) {
        return {
            "officiant": voices.filter((voice) => {
                return voice.name == "Microsoft Guy Online (Natural) - English (United States)";
            })[0],
            "respondent": voices.filter((voice) => {
                return voice.name == "Microsoft Jessa Online (Natural) - English (United States)";
            })[0]
        };
    }

    return {
        "officiant": voices.filter((voice) => {
            return voice.lang == "en-US";
        })[0],
        "respondent": voices.filter((voice) => {
            return voice.lang == "en-US";
        })[1],
    };
}


const voice = () => {
    window.addEventListener('unload', (event) => {
        window.speechSynthesis.cancel();
    });
    Array.from(document.querySelectorAll(".stop-button")).forEach((el) => {
        el.addEventListener("click", () => {
            window.speechSynthesis.cancel();
        });
    });
    Array.from(document.querySelectorAll(".play-button")).forEach((el) => {
        el.addEventListener("click", () => {
            window.speechSynthesis.cancel();
            const text = document.querySelector('#test-heading').innerText;
            // const text2 = "Hi Ben, does Google not accept long text."

            const msg = new SpeechSynthesisUtterance(text);
            const voices = getVoices();

            voices.then((voices) => {
                Array.from(document.querySelectorAll('.read')).forEach((el) => {
                    if (el.offsetParent !== null) {
                        let utterance = new SpeechSynthesisUtterance(el.innerText);
                        utterance.voice = voices['respondent'];
                        if (el.classList.contains('read-leader')) {
                            utterance.voice = voices['officiant'];
                        }
                        document.querySelector('#messages').innerText = document.querySelector('#messages').innerText + " " + utterance.voice.name
                       // window.speechSynthesis.speak(utterance)
                        //artyom.say(el.innerText)
                        quickStart();
                    }

                });
            })



            //     s.then((voices) => {
            //         // console.log(voices);
            //         // let voice = voices[1];
            //         // let possible_voices = voices.filter((voice) => {
            //         //     return voice.name.includes('Google')
            //         // });
            //         // if (possible_voices.length >= 1) {
            //         //       voice = possible_voices[0];
            //         // } else {
            //         //     let possible_voices = voices.filter((voice) => {
            //         //         return voice.name.includes('Microsoft')
            //         //     });
            //         //     if (possible_voices.length >= 1) {
            //         //         voice = possible_voices[1];
            //         //     }
            //         // }
            //         // console.log(voice);
            //         msg.lang = "en-US";
            //         msg.voice = voice;
            //         // msg.volume = 1;
            //         //
            //         // msg.rate = 1;
            //         msg.onend = function(e) {
            //             console.log('Finished in ' + event.elapsedTime + ' seconds.');
            //           };
            //         console.log(msg);
            //         window.speechSynthesis.speak(msg);
            //         console.log('done');
            //     });
            //
        })
    });
}

export {voice};
export GOOGLE_APPLICATION_CREDENTIALS="[PATH]"

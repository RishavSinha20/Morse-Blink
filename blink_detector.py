import cv2
import mediapipe as mp
import time

class BlinkDetector:
    def __init__(self, filename='detected_letters.txt'):
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_facemesh = mp.solutions.face_mesh
        self.facemesh = self.mp_facemesh.FaceMesh(max_num_faces=2)
        self.draw_spec = self.mp_draw.DrawingSpec(thickness=1, circle_radius=2)
        self.filename = filename
        self.last_blink_time = 0
        self.last_open_time = 0
        self.blink_threshold = 0.3  # Blink duration threshold in seconds
        self.pause_threshold = 2
        self.closed_eyes_duration = 0  # Duration of closed eyes
        self.save_duration_threshold = 7  # Save duration threshold in seconds
        self.blink_sequence = ""
        self.detected_letters = ""
        self.blink_separator = ''  # Separator to distinguish between short and long blinks
        self.dec_let=''
        self.toSend=False

        # Morse Code Dictionary
        self.morse_code = {
            "SL": "A",
            "LSSS": "B",
            "LSLS": "C",
            "LSS": "D",
            "S": "E",
            "SSLS": "F",
            "LLS": "G",
            "SSSS": "H",
            "SS": "I",
            "SLLL": "J",
            "LSL": "K",
            "SLSS": "L",
            "LL": "M",
            "LS": "N",
            "LLL": "O",
            "SLLS": "P",
            "LLSL": "Q",
            "SLS": "R",
            "SSS": "S",
            "L": "T",
            "SSL": "U",
            "SSSL": "V",
            "SLL": "W",
            "LSSL": "X",
            "LSLL": "Y",
            "LLSS": "Z",
            "SLSL": " ",
            "SSSSSS": "<BS>",
        }

    def calculate_ear(self, faceLm, index1, index2, index3, index4, index5, index6):
        # Calculate numerator part 1
        diff_x_1 = (faceLm.landmark[index1].x - faceLm.landmark[index2].x) ** 2
        diff_y_1 = (faceLm.landmark[index1].y - faceLm.landmark[index2].y) ** 2
        numerator_part1 = abs(diff_x_1 - diff_y_1)

        # Calculate numerator part 2
        diff_x_2 = (faceLm.landmark[index3].x - faceLm.landmark[index4].x) ** 2
        diff_y_2 = (faceLm.landmark[index3].y - faceLm.landmark[index4].y) ** 2
        numerator_part2 = abs(diff_x_2 - diff_y_2)

        # Calculate denominator
        diff_x_denom = (faceLm.landmark[index5].x - faceLm.landmark[index6].x) ** 2
        diff_y_denom = (faceLm.landmark[index5].y - faceLm.landmark[index6].y) ** 2
        denominator = abs(diff_x_denom - diff_y_denom)

        # Calculate eye aspect ratio (EAR)
        ear = (numerator_part1 + numerator_part2) / denominator

        return ear

    def process_frame(self, frame):
        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.facemesh.process(imgRGB)
        return results

    def save_to_file(self, text):
        with open(self.filename, 'a') as file:
            file.write(text)

    def backspace_from_file(self):
        try:
            # Open the file in read mode to read the content
            with open(self.filename, 'r') as file:
                content = file.read()
            
            # Check if there are characters in the file
            if content:
                # Open the file in write mode to rewrite the content after backspacing
                with open(self.filename, 'w') as file:
                    # Remove the last character from the content
                    new_content = content[:-1]
                    # Write the modified content back to the file
                    file.write(new_content)
                    print("Backspaced from the text file:", new_content[-1], flush=True)
            else:
                print("File is empty, cannot backspace.", flush=True)
        except IOError:
            print("Error: Unable to read or write to file.", flush=True)
    
    def decode_morse(self, blink_sequence):
        self.dec_let = self.morse_code[blink_sequence]
        # return dec_let

    def detect_blinks(self, frame):
        results = self.process_frame(frame)
        if results.multi_face_landmarks:
            for faceLm in results.multi_face_landmarks:
                ear1 = self.calculate_ear(faceLm, 160, 144, 158, 153, 33, 133)
                ear2 = self.calculate_ear(faceLm, 385, 380, 387, 373, 362, 263)

                if ear1 < 0.2 and ear2 < 0.2:
                    # self.hasBlinked=True  # Closed eyes
                    if self.last_blink_time == 0:
                        self.last_blink_time = time.time()
                    if self.last_open_time != 0:
                        self.last_open_time = 0
                        self.closed_eyes_duration = 0  # Reset closed eyes duration
                    self.closed_eyes_duration += 1 / 30  # Increment by frame rate
                    if self.closed_eyes_duration >= self.save_duration_threshold:
                        # Save to file
                        # self.save_to_file(self.detected_letters)
                        print("Saved to file:", self.filename, flush=True)
                        self.last_blink_time = 0
                        self.detected_letters = ""
                        return
                else: 
                    # Eyes are open
                    if self.last_open_time == 0:
                        self.last_open_time = time.time()
                    elif time.time() - self.last_open_time > self.pause_threshold:
                        if self.blink_sequence:
                            if self.blink_sequence in self.morse_code:
                                self.decode_morse(self.blink_sequence)
                                if self.dec_let == "<BS>":
                                    self.backspace_from_file()  # Backspace from the text file
                                    # self.dec_let='\b'
                                    self.toSend=True
                                else:
                                    self.detected_letters += self.dec_let
                                    self.save_to_file(self.dec_let)  # Save to file
                                    print("\nDetected letter:", self.dec_let, flush=True)
                                    self.toSend=True
                                    # self.hasBlinked=False 
                            self.blink_sequence = ''  # Reset blink sequence
                            print()
                        self.last_open_time = 0
                    if self.last_blink_time != 0:
                        blink_duration = time.time() - self.last_blink_time
                        if blink_duration >= self.blink_threshold:
                            if blink_duration > 0.8:  # Long blink
                                print('L', end='', flush=True)
                                self.blink_sequence += 'L'
                            else:  # Short blink
                                print('S', end='', flush=True)
                                self.blink_sequence += 'S'
                            self.last_blink_time = 0
        # return False
    def returnLetter(self):
        return self.detected_letters

    def release(self):
        self.facemesh.close()

# Example usage:
if __name__ == "_main_":
    detector = BlinkDetector()
    cap = cv2.VideoCapture(0)

    while True:
        success, frame = cap.read()
        if not success:
            break
        
        to_break = detector.detect_blinks(frame)
        print("word: ",detector.returnLetter())

        cv2.imshow("Frame", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): 
            break
        if to_break:
            break

    detector.release()
    cap.release()
    cv2.destroyAllWindows()
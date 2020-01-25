from imutils.video import VideoStream
import face_recognition
import argparse
import imutils
import pickle
import time
import cv2
# packages nécessaires pour la gestion des emails
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


ap = argparse.ArgumentParser()
ap.add_argument("-e", "--encodings", required=True,
            help="path to serialized db of facial encodings")
ap.add_argument("-i", "--output-img", type=str,
          help="path to output image")
ap.add_argument("-d", "--detection-method", type=str, default="hog",
            help="face detection model to use: either `hog` or `cnn`")
args = vars(ap.parse_args())

# # # #
#  Chargement des visages
#
print("[INFO] loading encodings…")
data = pickle.loads(open(args["encodings"], "rb").read())

# # # #
# Initialisation de la caméra
#
print("[INFO] Intitialize the camera…")
vs = VideoStream(usePiCamera=1).start()

# # # #
# Warmup de la caméra
#
print("[INFO] Camera warmup…")
time.sleep(2.0)

while True:
    # # # #
    # Lecture image actuelle
    #
    frame = vs.read()

    # # # #
    # Conversion couleurs BGR en RGB pour OpenCV.
    # Redimensionnement de la largeur de l’image
    # pour optimiser les temps de traitements
    #
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    rgb = imutils.resize(frame, width=250)
    r = frame.shape[1] / float(rgb.shape[1])

    # # # #
    # Récupération de la hitbox pour chaque visage
    #
    boxes = face_recognition.face_locations(rgb, model=args["detection_method"])

    # # # #
    # Encodage des visages trouvés
    # Cette étape peut être longue selon le nombre de 
    # visages trouvés
    #
    encodings = face_recognition.face_encodings(rgb, boxes)


    # # # #
    # Pour chaque img encodée on associe l’encodage + nom
    #
    names = []
    for encoding in encodings:
        # # # #
        # Comparaison du visage encodé actuel avec le
        # dataset
        #
        matches = face_recognition.compare_faces(data["encodings"],
            encoding)
        name = "Unknown"

        # # # #
        # Si ça match, c’est qu’il y a une comparaison
        # trouvée
        #
        if True in matches:
    
            # On récupère tous les éléments correspondants
            # au match
            matchedIdxs = [I for (I, b) in enumerate(matches) if b]
            counts = {}

            # Pour chaque match, récupération nom +
            # incrémentation "probabilité"
            for I in matchedIdxs:
                name = data["names"][I]
                counts[name] = counts.get(name, 0) + 1

            # Contrôle et récupération du nom 
            name = max(counts, key=counts.get)
        else:
            # Envoie de mail a adresse.mail@gmail.com
            # en cas de detection de Unknow
            msg = MIMEMultipart()
            msg['From'] = 'adresse.mail@gmail.com'
            msg['To'] = 'adresse.mail@gmail.com'
            msg['Subject'] = 'Intrusion' 
            message = 'Visage inconnu detecte'
            msg.attach(MIMEText(message))
            mailserver = smtplib.SMTP('smtp.gmail.com', 587)
            mailserver.ehlo()
            mailserver.starttls()
            mailserver.ehlo()
            mailserver.login('adresse.mail@gmail.com', 'MotDePasseMail')
            mailserver.sendmail('adresse.mail@gmail.com', 'adresse.mail@gmail.com', msg.as_string())
            mailserver.quit()
        
        # Sauvegarde
        names.append(name)

    # # # #
    # Dessin des cadres autour des têtes détectées 
    #
    for ((top, right, bottom, left), name) in zip(boxes, names):
        # redimensionnement
        top = int(top * r)
        right = int(right * r)
        bottom = int(bottom * r)
        left = int(left * r)

        # dessin du rectangle et du nom
        cv2.rectangle(frame, (left, top), (right, bottom),
            (0, 255, 0), 2)
        y = top - 15 if top - 15 > 15 else top + 15
        cv2.putText(frame, name, (left, y), cv2.FONT_HERSHEY_SIMPLEX,
            0.75, (0, 255, 0), 2)

    # Sauvegarde en tant qu’image 
    if args["output_img"] is not None:
        cv2.imwrite(args["output_img"], frame)

cv2.destroyAllWindows()
vs.stop()

import numpy as np
import cv2
from PIL import Image, ImageEnhance
import subprocess
import os
import sys
import shutil
import argparse


parser = argparse.ArgumentParser(description='prepare_video.py')

parser.add_argument('-i', '--input', dest='input_name', type=str, required=True, 
                    help="Path, name and filetype of video to make brighter")
parser.add_argument('-o', '--output', dest='output_name', type=str,
                    default='restored.avi', 
                    help="Path, name and filetype of output file")
# parser.add_argument('-m', '--mode', dest='mode', type=str, required=True, choices=['slice','merge'],
#                     help="Execution mode. 'slice' to split into frames, 'merge' to join frames.")                    

parsed = parser.parse_args()
input_name = parsed.input_name
output_name = parsed.output_name
# mode = parsed.mode

# Verificar se a entrada do programa é válida
if input_name.endswith('mp4') or input_name.endswith('avi'):
    video = input_name
else:
    print("Para executar o script entre com um arquivo no formato mp4 ou avi.")
    sys.exit(1)


# Código que verifica se o programa ffmpeg está instalado na máquina
try:
    subprocess.check_output(['which','ffmpeg'])
except:
    print("Instale o ffmpeg para execução do script.")
    sys.exit(1)


# Função que cria um diretório temporário para armazenar os arquivos
def create_tempdir():
    try:
        os.mkdir('./temp/')
    except OSError as e:
        print(e)

# Função que extrai o áudio do vídeo e armazena no diretório de arquivos temporários
def extract_audio(input_name):
    args = ['ffmpeg',
        '-i', '{}'.format(input_name),
        '-ab', '160k', 
        '-ac', '2', 
        '-ar', '44100', 
        '-vn', './temp/{}wav'.format(input_name[:-3])]
    
    try:
        p = subprocess.call(args)
    except:
        print("Falha ao extrair o áudio.")
        sys.exit(1)


def load_video(video):
    cap = cv2.VideoCapture(video)
    if not cap:
        print("Falha ao carregar o vídeo.")
        sys.exit(1)
    fps = cap.get(cv2.CAP_PROP_FPS)
    return cap, fps


def frames_to_png(cap):
    f = 0
    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret==True:
            f += 1

            # Convert cv2 image to rgb and load from numpy array
            frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)

            # # Enhance brightness
            # img = ImageEnhance.Brightness(img)
            # img = img.enhance(int(brightness))

            # # Convert back to bgr numpy array and write to disk
            frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            cv2.imwrite('./temp/frame{}.png'.format(str(f)),frame)
        else:
            break
    cap.release()


def png_to_mp4(framerate):
    framerate = str(framerate)
    
    args = ["ffmpeg",
        "-framerate", framerate,
        "-r", framerate,
        "-i","./temp/frame%d.png",
        "-vcodec","png",
        "./temp/0vid.mp4"]

    try:
        p = subprocess.call(args)
    except Exception as e:
        print(e)
        print("Falha ao converter png para mp4.")
        sys.exit(1)


def make_avi():
    args = [
        "ffmpeg",
        "-i","./temp/0vid.mp4",
        "-i","./temp/{}wav".format(input_name[:-3]),
        "-vcodec","copy",
        "-acodec","copy",
        "{}avi".format(output_name[:-3])
    ]

    try:
        p = subprocess.call(args)
    except:
        print("Falha ao criar avi.")
        sys.exit(1)


def make_mp4():
    args = [
        "ffmpeg",
        "-i","{}avi".format(output_name[:-3]),
        "-b:a","128k",
        "-vcodec","mpeg4",
        "-b:v","1200k",
        "-flags","+aic+mv4",
        output_name
    ]

    try:
        p = subprocess.call(args)
    except:
        print("Falha ao criar mp4.")
        sys.exit(1)


def cleanup():
    try:
        shutil.rmtree('./temp')
    except:
        print("Falha ao limpar diretório temporário.")

# Função que realiza a restauração nas imagens
def restore():
    args = [
        "python", "restore_images.py"
        "--input_folder","./temp",
        "--output_folder","./temp",
        "--GPU","0",
    ]

    try:
        p = subprocess.call(args)
    except:
        print("Falha ao realizar restauração.")
        sys.exit(1)

def main():
    create_tempdir()
    extract_audio(video)
    stream, framerate = load_video(video)
    frames_to_png(stream)
    restore()
    png_to_mp4(framerate)
    make_avi()
    if output_name.endswith('mp4'):
        make_mp4()
        os.remove('{}avi'.format(output_name[:-3]))
    cleanup()


if __name__ == '__main__':
    main()
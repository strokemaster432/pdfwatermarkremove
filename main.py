import fastapi

from fastapi import File, UploadFile, FastAPI
import uvicorn
from pathlib import Path

from fastapi.responses import FileResponse
import time

import shutil
from collections import defaultdict
from fastapi.responses import HTMLResponse
from typing import List


######## global variables ########
outputDir = "output/"
def nested_dict(): return defaultdict(nested_dict)

################################


app = FastAPI(title="pdf watermark remover", version="0.1")


@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(f'{process_time:0.4f} sec')
    return response


@app.post('/uploadfiles/')
def upload_car_file(files: List[UploadFile] = File(...)):
    # responses: list = []
    try:
        output_file = run_jar_file(files)
        return file_response_from_paths(output_file)
    except Exception as x:
        return fastapi.Response(content=str(x), status_code=500)


def run_jar_file(files):
    import os

    print("cleaning files")
    os.system("rm -rf output/*")
    os.system("rm -rf files/*")
    for i, f in enumerate(files):
        saved_obj = create_upload_file_sync(f)
        input_filename = saved_obj["location"]

        output_filename = getOutputFileName(f.filename)
        print(input_filename, output_filename)
        command = " java -jar ./pdf-strip-watermark.jar " + input_filename + \
            " " + output_filename + "  'match:.*gmail\.com.*' "
        os.system(command)
    return output_filename


@app.get("/")
async def main():
    content = """
    <body>
    Please upload your pdf file here from which watermark has to be removed.
    (It assumes that watermark is some gmail id.) sample : acb@gmail.com 

    Please upload only one pdf file at a time.
        <form action="/uploadfiles/" enctype="multipart/form-data" method="post">
        <input name="files" type="file" multiple>
        <input type="submit">
        </form>
    </body>
    """
    return HTMLResponse(content=content)


########## helper functions #######################

def file_response_from_paths(output_file_name):
    return FileResponse(getAbsolutePath(output_file_name))


def create_upload_file_sync(uploaded_file: UploadFile = File(...)):
    file_location = f"files/{uploaded_file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(uploaded_file.file, file_object)
    return {"info": f"file '{uploaded_file.filename}' saved at '{file_location}'", "location": f"{file_location}"}


def getAbsolutePath(filenamestring):
    path = Path(filenamestring).absolute()
    print(path, "\n\n")
    return path


def getOutputFileName(fstring):
    name = fstring.split(".")
    return outputDir + name[0] + ".pdf"


################################################


def configure(app):
    pass


if __name__ == '__main__':
    uvicorn.run(app, port=8000, host='0.0.0.0')
else:
    configure(app)

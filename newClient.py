"""Client to send requests to the server modified to take a whole directory
"""

import argparse
import json
import os
import time
from multiprocessing import freeze_support

import requests


def sendRequest(host: str, port: int, fpath: str, mdata: str):
    """Sends a classification request to the server.

    Args:
        host: Host address of the server.
        port: Port for the request.
        fpath: File path of the file to be analyzed.
        mdata: Additional json metadata.

    Returns:
        The json decoded response.
    """
    url = f"http://{host}:{port}/analyze"

    print(f"Requesting analysis for {fpath}")

    # Make payload
    with open(fpath, "rb") as audio_file:
        multipart_form_data = {
            "audio": (os.path.basename(fpath), audio_file),
            "meta": (None, mdata)
        }

        # Send request
        start_time = time.time()
        response = requests.post(url, files=multipart_form_data)
        end_time = time.time()

        print(f"Response: {response.text}, Time: {end_time - start_time:.4f}s", flush=True)

        # Convert to dict
        data = json.loads(response.text)

    return data


def saveResult(data, fpath):
    """Saves the server response.

    Args:
        data: The response data.
        fpath: The path to save the data at.
    """
    # Make directory
    dir_path = os.path.dirname(fpath)
    os.makedirs(dir_path, exist_ok=True)

    # Save result
    with open(fpath, "w") as f:
        json.dump(data, f, indent=4)


if __name__ == "__main__":
    # Freeze support for executable
    freeze_support()

    # Parse arguments
    parser = argparse.ArgumentParser(description="Client that queries an analyzer API endpoint server.")
    parser.add_argument("--host", default="localhost", help="Host name or IP address of API endpoint server.")
    parser.add_argument("--port", type=int, default=8080, help="Port of API endpoint server.")
    parser.add_argument("--i", default="example/", help="Path to directory with audio files to be analyzed.")
    parser.add_argument("--o", default="", help="Path to directory for saving result files. Leave blank to save with audio files.")
    parser.add_argument("--lat", type=float, default=-1, help="Recording location latitude. Set -1 to ignore.")
    parser.add_argument("--lon", type=float, default=-1, help="Recording location longitude. Set -1 to ignore.")
    parser.add_argument(
        "--week",
        type=int,
        default=-1,
        help="Week of the year when the recording was made. Values in [1, 48]. Set -1 for year-round species list."
    )
    parser.add_argument(
        "--overlap",
        type=float,
        default=0.0,
        help="Overlap of prediction segments. Values in [0.0, 2.9]. Defaults to 0.0."
    )
    parser.add_argument(
        "--sensitivity",
        type=float,
        default=1.0,
        help="Detection sensitivity; Higher values result in higher sensitivity. Values in [0.5, 1.5]. Defaults to 1.0."
    )
    parser.add_argument("--pmode", default="avg", help="Score pooling mode. Values in ['avg', 'max']. Defaults to 'avg'.")
    parser.add_argument("--num_results", type=int, default=5, help="Number of results per request. Defaults to 5.")
    parser.add_argument(
        "--sf_thresh",
        type=float,
        default=0.03,
        help="Minimum species occurrence frequency threshold for location filter. Values in [0.01, 0.99]. Defaults to 0.03."
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Define if files should be stored on server."
    )

    args = parser.parse_args()

    # Make metadata
    mdata = {
        "lat": args.lat,
        "lon": args.lon,
        "week": args.week,
        "overlap": args.overlap,
        "sensitivity": args.sensitivity,
        "sf_thresh": args.sf_thresh,
        "pmode": args.pmode,
        "num_results": args.num_results,
        "save": args.save
    }

    # Set input directory path
    input_directory = args.i

    # If output directory is not specified, save results in the input directory with the audio files
    output_directory = args.o if args.o else input_directory

    # Iterate through each file in the input directory
    for audio_file in os.listdir(input_directory):
        # Only process audio files with supported extensions (e.g., .wav)
        if audio_file.endswith(".wav") or audio_file.endswith(".mp3"):
            # Full path of the audio file
            audio_file_path = os.path.join(input_directory, audio_file)
            
            # Send a request to the server for each audio file
            data = sendRequest(args.host, args.port, audio_file_path, json.dumps(mdata))

            # Determine the output path for saving results
            result_file_path = os.path.join(
                output_directory,
                f"{os.path.splitext(audio_file)[0]}.BirdNET.results.json"
            )

            # Save the results
            saveResult(data, result_file_path)

 # A few examples to test
    # python3 client.py --host localhost --port 8080 --i example/soundscape.wav
    # python3 client.py --host localhost --port 8080 --i example/soundscape.wav --save --lat 42.5 --lon -76.45 --week 4
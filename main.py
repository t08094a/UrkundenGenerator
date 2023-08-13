#!/usr/bin/env python3

import logging
import argparse
import pathlib
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from lxml import etree


def generate_urkunde(urkunde: str, name: str, output: str):
    file_name_svg = "Urkunde " + name + '.svg'
    file_name_pdf = "Urkunde " + name + '.pdf'
    target_file_svg = os.path.join(output, file_name_svg)
    target_file_pdf = os.path.join(output, file_name_pdf)

    if os.path.exists(target_file_svg) or os.path.exists(target_file_pdf):
        logging.info(f'delete existing Urkunde: {name}')

        if os.path.exists(target_file_svg):
            os.remove(target_file_svg)
        if os.path.exists(target_file_pdf):
            os.remove(target_file_pdf)

    shutil.copyfile(urkunde, target_file_svg)

    logging.info(f'create Urkunde: {name}')

    svg_ns = "{http://www.w3.org/2000/svg}"

    with open(target_file_svg, 'r') as source_file:
        tree = etree.parse(source_file)

    node = tree.find('//{0}text[@id="Teilnehmer"]/{0}tspan'.format(svg_ns))
    node.text = name

    with open(target_file_svg, 'wb') as target:
        tree.write(target, encoding="utf-8", xml_declaration=True) # , pretty_print=True

    inkscape_command = (f'inkscape "{target_file_svg}" --export-area-page --batch-process --export-type=pdf '
                        f'--export-filename="{target_file_pdf}" 2>/dev/null')
    subprocess.call(inkscape_command, shell=True)

    logging.info(f'created Urkunde {name}')

    os.remove(target_file_svg)


def parse_arguments():
    parser = argparse.ArgumentParser(prog='main.py', usage='%(prog)s [options]',
                                     description='Generiert Urkunden für Teilnehmer definiert in einer Liste')
    parser.add_argument('urkunde', help='Ausgangsurkunde als SVG (*.svg) mit Textelement Id: Teilnehmer',
                        type=pathlib.Path)
    parser.add_argument('teilnehmerliste', help='Teilnehmerliste als Textdatei (*.txt) mit Namen der Teilnehmer pro '
                                                'Zeile', type=pathlib.Path)
    parser.add_argument('output', default='Urkunden_generiert', help='Ausgabeverzeichnis für die generierten Dateien',
                        type=pathlib.Path)
    local_args = parser.parse_args()
    return local_args


def parse_teilnehmerliste(filename: str) -> list[str]:
    with open(filename, 'r') as file:
        lines = filter(None, (line.rstrip() for line in file))
        return list(lines)


if __name__ == '__main__':
    log_format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=log_format, level=logging.INFO, datefmt="%H:%M:%S")
    logging.getLogger().setLevel(logging.DEBUG)

    args = parse_arguments()

    urkunde_file = os.path.realpath(args.urkunde)
    output_dir = os.path.realpath(args.output)
    teilnehmer_list: list[str] = parse_teilnehmerliste(args.teilnehmerliste)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(generate_urkunde(urkunde_file, teilnehmer, output_dir)) for teilnehmer in teilnehmer_list]
        wait(futures, timeout=60 * 10, return_when=ALL_COMPLETED)

    logging.info("Finished.")

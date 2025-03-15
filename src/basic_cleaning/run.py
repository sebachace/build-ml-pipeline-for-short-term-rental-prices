#!/usr/bin/env python


"""
Get data from wandb and save in temporary path,
 apply basic cleaning and reupload to wandb
Author: Sebastian Chace
Data: Dec 2022
"""

import argparse
import logging
import os
import wandb
import pandas as pd
# libraries ordered via pylint

logging.basicConfig(level=logging.INFO,
                     format= "%(asctime)-15s %(message)s")
logger = logging.getLogger()


def main_f(args):

    run = wandb.init(job_type="basic_cleaning")
    run.config.update(args)

    # Download input artifact. This will also log that this script is using this
    # particular version of the artifact
    # fetch file from wandb
    artifact_local_path = run.use_artifact(args.input_artifact).file()

    dataframe = pd.read_csv(artifact_local_path, index_col="id")
    min_price = args.min_price
    max_price = args.max_price
    idx = dataframe['price'].between(min_price, max_price)
    dataframe = dataframe[idx].copy()
    logger.info("price: Remove outliers beyond range: %s-%s",
                 args.min_price, args.max_price)
    dataframe['last_review'] = pd.to_datetime(dataframe['last_review'])
    logger.info("last_review: Correct data type")
    # drop rows with nonsense geolocation
    idx = dataframe['longitude'].between(-74.25, -73.50) & dataframe['latitude'].between(40.5, 41.2)
    dataframe = dataframe[idx].copy()

    # saving artifact locally
    tmp_artifact_path = os.path.join(args.tmp_directory, args.output_artifact)
    dataframe.to_csv(tmp_artifact_path, index=False)
    logger.info("Temporary artifact saved to %s" , tmp_artifact_path)

    artifact = wandb.Artifact(
        args.output_artifact,
        type=args.output_type,
        description=args.output_description
    )

    # saving artifact to wandb
    artifact.add_file(tmp_artifact_path)
    run.log_artifact(artifact)

    artifact.wait()
    logger.info("Clean dataset uploaded to wandb")


if __name__ == "__main__":
    # We're going to construct a parser by argument, and then compile them and call our main_f function
    parser = argparse.ArgumentParser(description="Perform basic data cleaning")

    parser.add_argument(
        "--tmp_directory",
        type=str,
        help="Temporary directory locally",
        required=True
    )
    parser.add_argument(
        "--input_artifact",
        type=str,
        help="Input artifact name",
        required=True
    )
    parser.add_argument(
        "--output_artifact",
        type=str,
        help="Output artif. name",
        required=True)
    parser.add_argument(
        "--output_type",
        type=str,
        help="Output artif. type",
        required=True)
    parser.add_argument(
        "--output_description",
        type=str,
        help="Output artif. description",
        required=True)

    parser.add_argument(
        "--min_price",
        type=int,
        help="Min. price limit",
        required=True
    )

    parser.add_argument(
        "--max_price",
        type=int,
        help="Max. price limit",
        required=True
    )

    args = parser.parse_args()

    main(args)

    main_f(args)

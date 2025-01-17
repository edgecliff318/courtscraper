import logging
from datetime import timedelta

import dash_ag_grid as dag
import dash_mantine_components as dmc
import pandas as pd
from dash import dcc, html

from src.core.config import get_settings
from src.db import bucket
from src.models.cases import Case

logger = logging.getLogger(__name__)
settings = get_settings()


def get_case_documents(case: Case):
    logger.info(f"Getting the documents for case {case.case_id}")

    # Get the documents from the dockets on Case Net
    if case.documents is not None and len(case.documents) > 0:
        documents = pd.DataFrame(case.documents)
    else:
        documents = pd.DataFrame(
            columns=["docket_desc", "file_path", "document_extension"]
        )

    # Get the case dockets
    if case.dockets is not None and len(case.dockets) > 0:
        dockets = pd.DataFrame(case.dockets)
        dockets = dockets[
            ["docket_desc", "filing_partyfullname", "filing_date"]
        ]
    else:
        dockets = pd.DataFrame(
            columns=["docket_desc", "filing_partyfullname", "filing_date"]
        )

    documents["source"] = "Casenet"

    # Get the pushed and uploaded documents
    documents_case = bucket.list_blobs(
        prefix=f"cases/{case.case_id}/", delimiter="/"
    )

    if documents_case is not None:
        documents_case = [
            {
                "docket_desc": document.name.split("/")[-1],
                "file_path": document.name,
                "document_extension": document.name.split(".")[-1],
                "source": "Uploaded/Generated",
                "updated": document.updated,
            }
            for document in documents_case
        ]
        documents_case = pd.DataFrame(documents_case)
        documents = pd.concat([documents, documents_case])

    columns = ["docket_desc", "file_path", "document_extension", "source"]
    documents = documents[columns].rename(
        columns={
            "docket_desc": "Description",
            "file_path": "File Path",
            "document_extension": "Extension",
            "source": "Source",
        }
    )

    # Generate the link from Firebase bucket
    documents["File Path"] = documents["File Path"].apply(
        lambda x: (
            bucket.get_blob(x).generate_signed_url(
                expiration=timedelta(seconds=3600)
            )
        )
    )

    documents["File Path"] = documents["File Path"].apply(
        lambda x: (f"[Download]" f"({x})")
    )

    column_defs = [
        {
            "field": "Description",
            "sortable": True,
            "filter": True,
            "flex": 1,
        },
        {
            "field": "File Path",
            "sortable": True,
            "filter": True,
            "flex": 1,
            "sortable": True,
            "resizable": True,
            "cellRenderer": "markdown",
        },
        {
            "field": "Extension",
            "sortable": True,
            "filter": True,
            "flex": 1,
        },
        {
            "field": "Source",
            "sortable": True,
            "filter": True,
            "flex": 1,
        },
    ]
    documents_ag_grid = dag.AgGrid(
        id="portfolio-grid",
        columnDefs=column_defs,
        rowData=documents.to_dict("records"),
        # Fit to content
        columnSize="sizeToFit",
        style={"height": 400},
    )

    # Part where the user can upload the case documents

    document_upload = dcc.Upload(
        id="documents-upload",
        children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
        style={
            "width": "100%",
            "height": "60px",
            "lineHeight": "60px",
            "borderWidth": "1px",
            "borderStyle": "dashed",
            "borderRadius": "5px",
            "textAlign": "center",
            "margin": "10px",
        },
        # Allow multiple files to be uploaded
        multiple=True,
    )

    dockets_list = dmc.Stack(
        [
            dmc.Group(
                [
                    dmc.Text(docket["docket_desc"], c="dark", fw=700),
                    dmc.Text(
                        f"By {docket['filing_partyfullname']} on {docket['filing_date']}"
                    ),
                ],
                gap="xs",
            )
            for docket in dockets.to_dict("records")
        ],
        gap="xs",
    )

    return dmc.Stack(
        [
            dmc.Title("Documents", order=3, className="mt-2"),
            documents_ag_grid,
            dmc.Title("Dockets Timeline", order=3, className="mt-2"),
            dockets_list,
            dmc.Title("Upload Documents", order=3, className="mt-2"),
            dmc.Stack(
                [html.Div(id="document-upload-status"), document_upload]
            ),
        ]
    )

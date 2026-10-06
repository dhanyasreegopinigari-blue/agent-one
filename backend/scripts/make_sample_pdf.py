from pathlib import Path

import pymupdf


def make_sample_pdf(output_path: Path) -> None:
    doc = pymupdf.open()

    pages_content = [
        # Page 1
        (
            "NORTHWIND SERVICES AGREEMENT\n\n"
            "This Services Agreement (the 'Agreement') is entered into and made effective as of 1 March 2025 "
            "('Effective Date'), by and between Northwind Ltd., a corporation incorporated under the laws of "
            "India ('Service Provider'), and Contoso Corp., a corporation organized and existing under the "
            "laws of Delaware ('Client').\n\n"
            "WHEREAS, Service Provider specializes in enterprise artificial intelligence consulting, system "
            "architecture, cloud infrastructure design, and computational engineering services; and\n\n"
            "WHEREAS, Client desires to retain Service Provider to perform certain professional services as "
            "described in Statements of Work issued hereunder, and Service Provider agrees to perform such "
            "services under the terms and conditions set forth herein.\n\n"
            "NOW, THEREFORE, in consideration of the mutual covenants, representations, warranties, and agreements "
            "contained herein, the parties hereto agree that the relationship commences on 1 March 2025."
        ),
        # Page 2
        (
            "SECTION 2: COMPENSATION AND PAYMENT TERMS\n\n"
            "2.1 Fees. Client agrees to pay Service Provider a fixed monthly fee of INR 450,000 for the core "
            "services outlined in Schedule A. All invoices shall be issued on the first business day of each "
            "calendar month.\n\n"
            "2.2 Taxes. All payments are exclusive of applicable taxes, including GST, which shall be added to "
            "invoices at the prevailing statutory rates.\n\n"
            "2.3 Late Payment. In the event that Client fails to remit payment within thirty (30) days of the "
            "invoice date, late interest of 1.5% per month (or the maximum permitted by law, whichever is lower) "
            "shall accrue on any overdue amount from the due date until full payment is received.\n\n"
            "2.4 Disputed Invoices. Client must notify Service Provider in writing within ten (10) days of invoice "
            "receipt of any good-faith dispute regarding fees charged."
        ),
        # Page 3
        (
            "SECTION 3: TERM AND TERMINATION\n\n"
            "3.1 Term. This Agreement shall commence on the Effective Date and shall remain in effect for an initial "
            "period of two (2) years unless terminated earlier in accordance with this Section 3.\n\n"
            "3.2 Termination for Convenience. Either party may terminate this Agreement or any Statement of Work "
            "without cause by providing at least 45 days written notice to the other party.\n\n"
            "3.3 Termination for Cause. Either party may terminate this Agreement immediately upon written notice if "
            "the other party materially breaches any provision of this Agreement and fails to cure such material "
            "breach within a cure period of 10 days following receipt of written notification specifying the breach.\n\n"
            "3.4 Effect of Termination. Upon termination, Client shall pay all outstanding fees for services "
            "performed up to the effective termination date."
        ),
        # Page 4
        (
            "SECTION 4: WARRANTIES AND LIMITATION OF LIABILITY\n\n"
            "4.1 Warranty. Service Provider warrants that all services will be performed in a professional, "
            "workmanlike manner consistent with standard industry practices.\n\n"
            "4.2 Disclaimer. EXCEPT AS EXPRESSLY PROVIDED HEREIN, NEITHER PARTY MAKES ANY WARRANTIES, EXPRESS, "
            "IMPLIED, STATUTORY OR OTHERWISE, INCLUDING ANY WARRANTIES OF MERCHANTABILITY OR FITNESS FOR A "
            "PARTICULAR PURPOSE.\n\n"
            "4.3 Liability Cap. To the maximum extent permitted by applicable law, the total cumulative aggregate "
            "liability of either party arising out of or related to this Agreement, whether in contract, tort, "
            "or under any other legal theory, shall be strictly capped at the total fees paid in the preceding "
            "12 months under this Agreement.\n\n"
            "4.4 Consequential Damages. In no event shall either party be liable for any indirect, incidental, "
            "punitive, or consequential damages."
        ),
        # Page 5
        (
            "SECTION 5: CONFIDENTIALITY AND PROPRIETARY INFORMATION\n\n"
            "5.1 Definition. 'Confidential Information' refers to all non-public information disclosed by one party "
            "to the other, whether orally or in writing, that is designated as confidential or that reasonably should "
            "be understood to be confidential given the nature of the information.\n\n"
            "5.2 Obligations. Each party agrees to protect the other party's Confidential Information with the same "
            "degree of care it uses for its own confidential information, but in no event less than reasonable care.\n\n"
            "5.3 Exclusions. Confidential Information does not include information that is publicly known, already in "
            "possession prior to disclosure, or independently developed without reference to the disclosing party's data.\n\n"
            "5.4 Survival. The obligations of confidentiality set forth in this Section 5 shall survive termination "
            "of this Agreement for a period of 3 years."
        ),
        # Page 6
        (
            "SECTION 6: GOVERNING LAW AND DISPUTE RESOLUTION\n\n"
            "6.1 Governing Law. This Agreement, and all claims or causes of action based upon, arising out of, or "
            "related to this Agreement, shall be governed by, and construed in accordance with, the substantive laws of "
            "Telangana, India, without regard to conflict of law principles.\n\n"
            "6.2 Dispute Resolution and Arbitration. Any dispute, controversy, or claim arising out of or relating to "
            "this contract, including the formation, interpretation, breach, or termination thereof, shall be referred "
            "to and finally resolved by binding arbitration under the Arbitration and Conciliation Act, 1996.\n\n"
            "6.3 Seat of Arbitration. The seat and legal venue of arbitration shall be Hyderabad.\n\n"
            "IN WITNESS WHEREOF, the authorized representatives of the parties have executed this Agreement."
        ),
    ]

    for text in pages_content:
        page = doc.new_page(width=600, height=800)
        page.insert_textbox(pymupdf.Rect(50, 50, 550, 750), text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))
    doc.close()
    print(f"Generated sample PDF at: {output_path}")


if __name__ == "__main__":
    out = Path(__file__).parent.parent / "eval" / "sample.pdf"
    make_sample_pdf(out)

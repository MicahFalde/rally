"""Ohio voter file adapter.

Ohio SOS provides free voter files at:
https://www6.ohiosos.gov/ords/f?p=VOTERFTP:HOME

Files are per-county, tab-delimited, with the following columns:
SOS_VOTERID, COUNTY_NUMBER, COUNTY_ID, LAST_NAME, FIRST_NAME, MIDDLE_NAME,
SUFFIX, DATE_OF_BIRTH, REGISTRATION_DATE, VOTER_STATUS, PARTY_AFFILIATION,
RESIDENTIAL_ADDRESS1, RESIDENTIAL_SECONDARY_ADDR, RESIDENTIAL_CITY,
RESIDENTIAL_STATE, RESIDENTIAL_ZIP, RESIDENTIAL_ZIP_PLUS4, RESIDENTIAL_COUNTRY,
RESIDENTIAL_POSTALCODE, MAILING_ADDRESS1, MAILING_SECONDARY_ADDRESS,
MAILING_CITY, MAILING_STATE, MAILING_ZIP, MAILING_ZIP_PLUS4, MAILING_COUNTRY,
MAILING_POSTAL_CODE, CAREER_CENTER, CITY, CITY_SCHOOL_DISTRICT, COUNTY_COURT_DISTRICT,
CONGRESSIONAL_DISTRICT, COURT_OF_APPEALS, EDU_SERVICE_CENTER_DISTRICT,
EXEMPTED_VILL_SCHOOL_DISTRICT, LIBRARY, LOCAL_SCHOOL_DISTRICT,
MUNICIPAL_COURT_DISTRICT, PRECINCT_NAME, PRECINCT_CODE, STATE_BOARD_OF_EDUCATION,
STATE_REPRESENTATIVE_DISTRICT, STATE_SENATE_DISTRICT, TOWNSHIP, UNION_TOWNSHIP,
VILLAGE, PRIMARY-03/19/2024, GENERAL-11/07/2023, ...
(vote history columns are dynamic, named by election)
"""
from datetime import date, datetime

from app.adapters.base import StateAdapter


# Ohio county FIPS-to-name mapping for the 88 counties
OHIO_COUNTIES = {
    "01": "ADAMS", "02": "ALLEN", "03": "ASHLAND", "04": "ASHTABULA",
    "05": "ATHENS", "06": "AUGLAIZE", "07": "BELMONT", "08": "BROWN",
    "09": "BUTLER", "10": "CARROLL", "11": "CHAMPAIGN", "12": "CLARK",
    "13": "CLERMONT", "14": "CLINTON", "15": "COLUMBIANA", "16": "COSHOCTON",
    "17": "CRAWFORD", "18": "CUYAHOGA", "19": "DARKE", "20": "DEFIANCE",
    "21": "DELAWARE", "22": "ERIE", "23": "FAIRFIELD", "24": "FAYETTE",
    "25": "FRANKLIN", "26": "FULTON", "27": "GALLIA", "28": "GEAUGA",
    "29": "GREENE", "30": "GUERNSEY", "31": "HAMILTON", "32": "HANCOCK",
    "33": "HARDIN", "34": "HARRISON", "35": "HENRY", "36": "HIGHLAND",
    "37": "HOCKING", "38": "HOLMES", "39": "HURON", "40": "JACKSON",
    "41": "JEFFERSON", "42": "KNOX", "43": "LAKE", "44": "LAWRENCE",
    "45": "LICKING", "46": "LOGAN", "47": "LORAIN", "48": "LUCAS",
    "49": "MADISON", "50": "MAHONING", "51": "MARION", "52": "MEDINA",
    "53": "MEIGS", "54": "MERCER", "55": "MIAMI", "56": "MONROE",
    "57": "MONTGOMERY", "58": "MORGAN", "59": "MORROW", "60": "MUSKINGUM",
    "61": "NOBLE", "62": "OTTAWA", "63": "PAULDING", "64": "PERRY",
    "65": "PICKAWAY", "66": "PIKE", "67": "PORTAGE", "68": "PREBLE",
    "69": "PUTNAM", "70": "RICHLAND", "71": "ROSS", "72": "SANDUSKY",
    "73": "SCIOTO", "74": "SENECA", "75": "SHELBY", "76": "STARK",
    "77": "SUMMIT", "78": "TRUMBULL", "79": "TUSCARAWAS", "80": "UNION",
    "81": "VAN WERT", "82": "VINTON", "83": "WARREN", "84": "WASHINGTON",
    "85": "WAYNE", "86": "WILLIAMS", "87": "WOOD", "88": "WYANDOT",
}


class OhioAdapter(StateAdapter):
    state_code = "OH"
    file_encoding = "latin-1"
    delimiter = ","

    def parse_row(self, row: dict) -> dict | None:
        voter_id = row.get("SOS_VOTERID", "").strip()
        if not voter_id:
            return None

        last_name = row.get("LAST_NAME", "").strip()
        first_name = row.get("FIRST_NAME", "").strip()
        if not last_name or not first_name:
            return None

        address = row.get("RESIDENTIAL_ADDRESS1", "").strip()
        city = row.get("RESIDENTIAL_CITY", "").strip()
        zip_code = row.get("RESIDENTIAL_ZIP", "").strip()
        if not address or not city:
            return None

        # Parse date of birth
        dob = None
        dob_raw = row.get("DATE_OF_BIRTH", "").strip()
        if dob_raw:
            for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
                try:
                    dob = datetime.strptime(dob_raw, fmt).date()
                    break
                except ValueError:
                    continue

        # Parse registration date
        reg_date = None
        reg_raw = row.get("REGISTRATION_DATE", "").strip()
        if reg_raw:
            for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y"):
                try:
                    reg_date = datetime.strptime(reg_raw, fmt).date()
                    break
                except ValueError:
                    continue

        # Parse vote history — Ohio has dynamic columns like "PRIMARY-03/19/2024"
        # Values: X = voted nonpartisan, D/R/L/G/etc = party declared in primary, blank = didn't vote
        vote_history = []
        for key, value in row.items():
            if not key:
                continue
            value = (value or "").strip()
            if not value:
                continue
            # Ohio vote history columns: "GENERAL-11/07/2023", "PRIMARY-03/19/2024"
            if key.startswith(("GENERAL-", "PRIMARY-", "SPECIAL-")):
                parts = key.split("-", 1)
                if len(parts) == 2:
                    election_type = parts[0].lower()
                    election_date = parts[1]
                    # Value indicates party pulled in primary, or X for nonpartisan/general
                    party_voted = None if value == "X" else value
                    vote_history.append({
                        "election": f"{election_date}-{election_type[:3].upper()}",
                        "type": election_type,
                        "party": party_voted,
                    })

        county_num = row.get("COUNTY_NUMBER", "").strip().zfill(2)
        county_name = OHIO_COUNTIES.get(county_num, row.get("COUNTY_NUMBER", "").strip())

        # Ohio uses district numbers directly
        state_house = row.get("STATE_REPRESENTATIVE_DISTRICT", "").strip()
        state_senate = row.get("STATE_SENATE_DISTRICT", "").strip()
        congressional = row.get("CONGRESSIONAL_DISTRICT", "").strip()

        zip_plus4 = row.get("RESIDENTIAL_ZIP_PLUS4", "").strip()
        full_zip = f"{zip_code}-{zip_plus4}" if zip_plus4 else zip_code

        return {
            "state_voter_id": voter_id,
            "first_name": first_name,
            "middle_name": row.get("MIDDLE_NAME", "").strip() or None,
            "last_name": last_name,
            "suffix": row.get("SUFFIX", "").strip() or None,
            "date_of_birth": dob,
            "gender": None,  # Ohio voter file doesn't include gender
            "address_line1": address,
            "address_line2": row.get("RESIDENTIAL_SECONDARY_ADDR", "").strip() or None,
            "city": city,
            "state_code": "OH",
            "zip_code": full_zip,
            "county": county_name,
            "party": self.normalize_party(row.get("PARTY_AFFILIATION")),
            "registration_date": reg_date,
            "voter_status": row.get("VOTER_STATUS", "ACTIVE").strip().lower(),
            "congressional_district": f"OH-{congressional}" if congressional else None,
            "state_senate_district": f"OH-SD-{state_senate}" if state_senate else None,
            "state_house_district": f"OH-HD-{state_house}" if state_house else None,
            "school_district": (
                row.get("CITY_SCHOOL_DISTRICT", "").strip()
                or row.get("LOCAL_SCHOOL_DISTRICT", "").strip()
                or row.get("EXEMPTED_VILL_SCHOOL_DISTRICT", "").strip()
                or None
            ),
            "precinct": row.get("PRECINCT_NAME", "").strip() or row.get("PRECINCT_CODE", "").strip() or None,
            "vote_history": vote_history if vote_history else None,
        }

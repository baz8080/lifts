"""What the Station Accessibility Programme business case says, station by station.

Iarnrod Eireann's preliminary business case to the NTA (PBC-3.5, final, 30
October 2024, published at nationaltransport.ie in May 2025) is the one public
document that lists which stations do not yet meet the accessibility standard,
in the order the programme means to fix them, and for the first fifteen
describes the station as it stood. Both are dated facts and both are carried
here so the questionnaire can put them in front of whoever answers it. The
seeder reads neither: this is context for a person, not a claim about a route.
`notes/step-free-graph.md`.
"""

from __future__ import annotations

PUBLISHER = "Iarnrod Eireann, Station Accessibility Programme Preliminary Business Case"
DATE = "2024-10-30"
SOURCE_KIND = "nta-pbc-2024-10"

# Table 6-2: the 51 stations seeking funding from 2022, by priority rank after
# the 2019 review. Carlow, Ennis and Edgeworthstown were complete by then;
# Connolly, Ashtown and Coolmine went to DART+; Limerick was done elsewhere.
STATIONS = {
    "DLKEY": (1, "Dalkey"),
    "GSTON": (2, "Gormanston"),
    "LSLND": (3, "Little Island"),
    "BTEER": (4, "Banteer"),
    "RMORE": (5, "Rathmore"),
    "MYNTH": (6, "Maynooth"),
    "GHANE": (7, "Glounthaune"),
    "RDRUM": (8, "Rathdrum"),
    "ARKLW": (9, "Arklow"),
    "ATHY": (10, "Athy"),
    "LFORD": (11, "Longford"),
    "RBROK": (12, "Rushbrooke"),
    "WLOW": (13, "Wicklow"),
    "BOYLE": (14, "Boyle"),
    "CLMRS": (15, "Claremorris"),
    "GOREY": (16, "Gorey"),
    "RSCMN": (17, "Roscommon"),
    "ECRTY": (18, "Enniscorthy"),
    "DRMOD": (19, "Dromod"),
    "RLSTD": (20, "Rosslare Strand"),
    "FFORE": (21, "Farranfore"),
    "MNEBG": (22, "Muine Bheag"),
    "FOTA": (23, "Fota"),
    "CSREA": (24, "Castlerea"),
    "BYHNS": (25, "Ballyhaunis"),
    "CGLOE": (26, "Carrigaloe"),
    "DCDRA": (27, "Drumcondra"),
    "BBRDG": (28, "Broombridge"),
    "KCOCK": (29, "Kilcock"),
    "LXLSA": (30, "Leixlip Louisa Bridge"),
    "CNOCK": (31, "Castleknock"),
    "TRLEE": (32, "Tralee"),
    "KCOOL": (33, "Kilcoole"),
    "SLIGO": (34, "Sligo"),
    "COBH": (35, "Cobh"),
    "LXCON": (36, "Leixlip Confey"),
    "ENFLD": (37, "Enfield"),
    "KLRNY": (38, "Killarney"),
    "RLEPT": (39, "Rosslare Europort"),
    "WXFRD": (40, "Wexford"),
    "MLSRT": (41, "Millstreet"),
    "COLNY": (42, "Collooney"),
    "FXFRD": (43, "Foxford"),
    "THTWN": (44, "Thomastown"),
    "CKOSH": (45, "Carrick-on-Shannon"),
    "BMOTE": (46, "Ballymote"),
    "BALNA": (47, "Ballina"),
    "WPORT": (48, "Westport"),
    "CLBAR": (49, "Castlebar"),
    "MNLAJ": (50, "Manulla Junction"),
    "MLGAR": (51, "Mullingar"),
}

# Appendix B, "Current context": the station as the programme found it, for the
# fifteen stations in the first five-year window, with the printed page number.
# Quoted verbatim; a delivery date in Appendix B's table says what has changed
# since ("Full Delivery (2025)" at Athy is why its page now names a lift).
DELIVERY = {
    "DLKEY": "Full Delivery (2022)",
    "GSTON": "Full Delivery (2022)",
    "LSLND": "Full Delivery (2023)",
    "BTEER": "Full Delivery (2024)",
    "RMORE": "Full Delivery (2024/2025)",
    "ATHY": "Full Delivery (2025)",
    "RDRUM": "Full Delivery (2025)",
    "MYNTH": "Full Delivery (2025)",
    "BOYLE": "Full Delivery (2025/2026)",
    "CLMRS": "Part Delivery 2026, complete 2027",
    "GHANE": "Part Delivery 2026, complete 2027",
    "RBROK": "Phase 5 Detailed Design (Year 6 completion)",
    "LFORD": "Phase 5 Detailed Design (Year 6 completion)",
    "ARKLW": "Phase 5 Detailed Design (Year 6 completion)",
    "WLOW": "Phase 5 Detailed Design (Year 6 completion)",
}

CONTEXT = {
    "DLKEY": (
        142,
        "Dalkey station is located in the town of Dalkey, County Dublin. The town is a suburb of "
        "Dublin, and the railway station is part of the DART suburban rail network, being served "
        "by trains on the Greystones to Howth and Malahide lines. In addition to being served by "
        "DART suburban services, the station is also served by intercity services between Dublin "
        "Connolly and Wexford/Rosslare Europort. The station has two platforms which are "
        "connected by a footbridge with steps but no accessible provision between the platforms. "
        "The footbridge is located near the centre of each platform. Both platforms at the "
        "station are accessible to passengers with reduced mobility. Accessible access to "
        "platform 2 (southbound) is via the station building and platform 1 (northbound) is via a "
        "ramp which connects to Ardeevin Road to the south of the station. A 70-space car park is "
        "available at the station but is located near the station building on platform 2. As a "
        "result, passengers with reduced mobility who wish to access platform 1 are required to "
        "exit the station, cross over the railway using the road bridge between Railway Road and "
        "Ardeevin Road and re-enter the station using the ramp on Ardeevin Road. The station has "
        "a ticket office which is manned for a period in the morning, and accessible ticket "
        "machines available when the ticket office is closed."
    ),
    "GSTON": (
        143,
        "Gormanston station is located next to Gormanston beach, approximately 1.15km away "
        "Gormanston village, County Meath. The station is served by services on the Dublin to "
        "Dundalk line, with some peak hour services extending south of Dublin to Bray. The "
        "station has two platforms which are not connected on IÉ property. Instead, passengers "
        "wishing to travel southbound must exit the station property, pass over a small road "
        "bridge which crosses the southern end of the station, and enter the station via a ramp "
        "behind Platform 1. Level access is possible to platform 2, making it possible for "
        "passengers with reduced mobility to travel northbound more easily but access to platform "
        "1 is restricted for passengers with reduced mobility as the ramp that leads down from "
        "the public road to the platform is not easily accessible due to its location and the "
        "camber of the road at the access point. The station is unmanned but ticket machines are "
        "available on the platforms."
    ),
    "LSLND": (
        144,
        "Little Island station is located next to the N25 dual-carriageway and the town and "
        "industrial area of Little Island, County Cork. The station is served by services on the "
        "Cork commuter network, with trains running from Mallow to Cobh and Midleton. The station "
        "has two platforms which are connected by a S-shaped footbridge, at the western end of "
        "the station, with steps but no accessible provision. The station has two car parks, with "
        "a total of 64 spaces (61 standard spaces and 3 accessible parking bays), both of which "
        "are located to the north of the station. Platform 1 (to Cobh and Midleton) can be "
        "accessed via a ramp from the car parks but the accessible route to Platform 2 (towards "
        "Cork) is via Island Corporate Park and the R623 road bridge which crosses the railway "
        "just to the east of the station. Passengers are then required to use a path down the "
        "edge of the N25 eastbound off-slip to access a ramp to the station. This means that the "
        "route is difficult for a person with reduced mobility to use if they are dropped off at "
        "the station car park. The station is unstaffed with the main station building being "
        "closed to the public, but a ticket machine, that is accessible to wheelchair users, is "
        "available on each platform at the station."
    ),
    "BTEER": (
        146,
        "Banteer station is located on the edge of the town of Banteer, County Cork. The station "
        "is served by services on the Mallow to Tralee line, with some services serving the "
        "station also extending to Cork and Dublin Heuston. The station has two platforms which "
        "are connected by a footbridge, located to the west of the existing station building with "
        "steps but no accessible provision that would provide step free access between the "
        "platforms. As a result, passengers with reduced mobility can access platform 1 "
        "(eastbound towards Mallow) but are unable to travel westbound (towards Tralee) from "
        "platform 2. The station has a small car park with 19 spaces (18 standard spaces and 1 "
        "accessible parking bay). There is also a large maintenance/siding area which stands "
        "adjacent to the station car park and is owned by IÉ. The station is staffed between "
        "07:00 and 16:00, Monday to Thursday, and between 06:00 and 15:00 on a Friday. Outside of "
        "these times there is also a ticket machine available at the station that is accessible "
        "to wheelchair users."
    ),
    "RMORE": (
        147,
        "Rathmore station is located in the town of Rathmore, County Kerry. The station is served "
        "by trains on the Mallow to Tralee line, with some services extending to Cork and Dublin "
        "Heuston. The station has two platforms which are connected by a footbridge, located to "
        "the western end of the station. The footbridge has steps between the platform and "
        "overbridge levels but no accessible provision that would provide step free access "
        "between the platforms. As a result, passengers with reduced mobility are able to travel "
        "on services stopping at platform 1, which has level access from the station car park but "
        "are unable to access platform 2. The station has a car park with 27 spaces and 2 "
        "accessible parking bays. The station has a staffed ticket office which is open between "
        "07:00 and 19:00 Monday to Saturday and between 08:00 and 19:00 on Sundays. Outside of "
        "these times ticket machines are available on the platforms which are accessible to "
        "wheelchair users. In addition to the car parking space, there is a small "
        "maintenance/siding area to the east of the station car park."
    ),
    "ATHY": (
        148,
        "Athy station is located in the centre of the town of Athy, County Kildare. The station "
        "is served by trains running on the Dublin Heuston to Waterford line. The station has two "
        "platforms which are connected by a footbridge located towards the northern end of the "
        "station. The footbridge has steps providing access between the platforms and the "
        "overbridge but no accessible provision that would allow step free access to both "
        "platforms. Step free access is available to platform 1 via a ramp from the station car "
        "park but no step free access is possible to Platform 2. The station has a car park with "
        "84 standard spaces and 4 accessible parking bays. The station has limited staff "
        "availability and does not have a booking office. Instead, tickets can be purchased from "
        "two ticket machines next to the station entrance. These ticket machines are accessible "
        "for wheelchair users."
    ),
    "RDRUM": (
        150,
        "Rathdrum station is located approximately 400m southeast of the centre of the village of "
        "Rathdrum, County Wicklow. The station is served by trains on the Dublin Connolly to "
        "Wexford/Rosslare Europort route. The station has two platforms which are connected by a "
        "footbridge, located near the centre of the platforms. The station is located in a "
        "cutting, meaning there is level access between the station car park and the overbridge "
        "with steps providing access down to both platforms. Platform 1 is accessible to "
        "passengers with reduced mobility via a ramp from the car park but there is no step-free "
        "access to Platform 2. Most trains that travel through Rathdrum use platform 1 where "
        "possible. However, in several instances trains are required to use platform 2 due to "
        "service requirements, and this means that these services are not accessible for "
        "passengers with reduced mobility. The station has a small car park with 20 spaces "
        "including one accessible parking bay. The station is unmanned but two ticket machines "
        "are available, with one being accessible for wheelchair users."
    ),
    "MYNTH": (
        151,
        "Maynooth station is located in the town of Maynooth, County Kildare. The station is "
        "served by trains on the Dublin Connolly to Sligo and Longford line, as well as "
        "additional services terminating at the station before returning to Dublin. The station "
        "has two platforms which are connected by a footbridge. The footbridge has steps on both "
        "sides but does not have accessible provision between the platform and cross-span of the "
        "footbridge. Accessible access to the platform 1 (towards Dublin) is via the main station "
        "building on the northern side of the station, while access to platform 2 (westbound) is "
        "via a ramp on the southern side of the station, opposite the main station building. The "
        "station is manned between 06:30 and 21:00 Monday-Saturday and 09:30-21:00 on Sundays and "
        "Public Holidays with toilets (including accessible facilities) available for passengers. "
        "The station also has a large car park with 222 spaces available, including 5 accessible "
        "parking spaces. In addition to the Station Accessibility Programme upgrades being "
        "brought forward at the station, Maynooth is also part of the DART+ West project, with "
        "additional upgrades planned as part of this scheme. DART+ upgrades include the "
        "installation of OHLE lines and stanchions that are required to run the new DART+ "
        "electric trains that will be introduced on the line. In addition to achieving "
        "accessibility compliance, the Station Accessibility Programme interventions at Maynooth "
        "have also been considered for their complementarity with the planned DART+ works."
    ),
    "BOYLE": (
        152,
        "Boyle station is located to the south of the town of Boyle, County Roscommon. The "
        "station is served by services on the Dublin Connolly to Sligo line. The station has two "
        "platforms which are connected by a footbridge near the eastern end of the station. The "
        "footbridge has steps to both platforms but no accessible provision that would provide "
        "step free access to both platforms. Step free access is available to the Dublin-bound "
        "platform, but no access is possible to the Sligo- bound platform. This means that "
        "passengers with restricted mobility who are looking to travel towards Sligo would not be "
        "able to board most trains at this station. The station has a car park with 55 standard "
        "spaces and 3 accessible parking bays. The station has a ticket office which is staffed "
        "between 07:00 and 15:30, Monday to Friday. Additionally, the station has two ticket "
        "machines which are accessible to wheelchair users."
    ),
    "CLMRS": (
        154,
        "Claremorris station is located in the town of Claremorris, County Mayo. The station is "
        "served by services on the Dublin Heuston to Westport and Ballina line. The station has "
        "three platforms (1 platform adjacent to the station car park, and one island platform "
        "with a running line on either side) that are connected by a footbridge at the southern "
        "end of the station. The footbridge has steps to both platforms but no accessible "
        "provision that would provide step free access to platforms 2 and 3. Most trains serving "
        "the station depart from platform 1, meaning that the services are accessible to "
        "passengers with restricted mobility. However, those services that call at platforms 2 or "
        "3 are not accessible to passengers with reduced mobility. The station has a small car "
        "park with 30 standard spaces and 2 accessible parking bays. The station has a ticket "
        "office but opening times are sometimes restricted. Outside of the ticket office opening "
        "hours, tickets can be purchased from ticket machines at the station entrance. One of "
        "these machines is accessible to wheelchair users."
    ),
    "GHANE": (
        155,
        "Glounthaune station is located approximately 750m east of the main village of "
        "Glounthaune, County Cork. The station is served by trains on the Cork suburban commuter "
        "network, with services running from Mallow to Cobh and Midleton. The station has two "
        "platforms which are connected by a footbridge, located at the eastern end of the "
        "station. The current footbridge has steps connecting the platforms to the overbridge, "
        "but no accessible provision that would provide step free access to both platforms. Due "
        "to the location of the station adjacent to Lough Mahon, there is no step-free access to "
        "Platform 2, meaning that passengers with reduced mobility are unable to travel "
        "westbound, towards Cork, from the station. As a result, passengers who require step free "
        "access and wish to board/alight Cork-bound services at the station must travel to the "
        "next accessible station on the route before changing onto the next available train to "
        "Glounthaune. This would mean that passengers with reduced mobility would potentially "
        "have to travel to Cork, Carrigtwohill or Cobh, depending on the destination of the "
        "train, before returning to Glounthaune. The station does not have a ticket office, but "
        "two ticket machines are available, with one being accessible for wheelchair users."
    ),
    "RBROK": (
        157,
        "Rushbrooke is located in the town of Rushbrooke, County Cork, adjacent to the Rushbrooke "
        "Commercial Park. The station is on the Cork commuter rail network, with trains running "
        "from Mallow to Cobh. The station has two platforms which are connected by a S-shaped "
        "footbridge with steps but no accessible provision that would provide step free access to "
        "both platforms. A ramp from the R624 at the front of the station provides step free "
        "access to platform 2 (for trains to Cork) but no access is possible to platform 1 (for "
        "trains towards Cobh). Passengers with reduced mobility who wish to board or alight "
        "trains from platform 1 must travel to the next accessible station along the line and "
        "then return to Rushbrooke on the other platform. Despite the step free access being "
        "available to platform 2, the station is likely to get limited use by persons with "
        "reduced mobility, as the station has no car park and a pedestrian route to the station "
        "would require most potential passengers to walk at least 400m via a road bridge to the "
        "nearby houses. A shorter pedestrian route is available to platform 1 but this does not "
        "provide step free access to the station. The station is unstaffed, but tickets can be "
        "purchased from a ticket machine on platform 2."
    ),
    "LFORD": (
        158,
        "Longford station is located in the centre of the town of Longford, County Longford. The "
        "station is on the Dublin Connolly to Sligo line, with a small number of peak hour "
        "services terminating at the station before returning to Dublin. The station has two "
        "platforms which are connected by a footbridge located at the western end of the station. "
        "The footbridge is inaccessible to persons of reduced mobility. However, both platforms "
        "could be accessible, with platform 1 accessible via a ramp from the station car park and "
        "platform 2 accessible via a lift from the Sráid an larla road bridge which lies at the "
        "western end of the station. While the lift structure on the Sráid an larla road bridge "
        "remains in place, this structure is not currently operational, meaning that step-free "
        "access to platform 2 could be limited. The station has a small car park with 27 standard "
        "spaces and 2 accessible parking bays. The station has previously had a staffed ticket "
        "office, but this is currently closed with ticket machines available for purchasing "
        "tickets. The ticket machines are accessible for wheelchair users."
    ),
    "ARKLW": (
        160,
        "Arklow station is located in the centre of the town of Arklow, County Wicklow. The "
        "station is served by services on the Dublin Connolly to Wexford/Rosslare Europort route. "
        "The station has two platforms which are connected by a footbridge with steps but no "
        "accessible provision that would provide step free access to both platforms. The "
        "footbridge is located approximately halfway along the station platform to the south of "
        "the existing station building. Level access is available to platform 1, which allows "
        "passengers to board southbound services but platform 2 is inaccessible to passengers "
        "with reduced mobility. This means that these passengers are unable to board services "
        "travelling northbound through the station. The station has a large car park with 125 "
        "standard spaces and 9 accessible parking bays. The station is staffed between 05:30 and "
        "21:00 and has a ticket office and toilet facilities which are available for passengers. "
        "Additionally, the station also has ticket machines which are accessible for wheelchair "
        "users."
    ),
    "WLOW": (
        162,
        "Wicklow station is located to the north of Wicklow, County Wicklow. The station is on "
        "the Dublin Connolly to Wexford/Rosslare Europort line. The station has two platforms "
        "connected by a footbridge with steps but no accessible provision that would provide step "
        "free access to both platforms. Level access is available to platform one on the southern "
        "side of the station but platform 2 can only be accessed by the footbridge. This means "
        "that trains stopping platform 2 are not accessible for passengers with reduced mobility. "
        "The station has a car park with 64 standard spaces and 4 accessible bays. The station is "
        "staffed throughout the day, with a ticket office and toilet facilities. Additionally, "
        "there are two ticket machines next to the station entrance which are accessible to "
        "wheelchair users."
    ),
}

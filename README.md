# IBM_Cloudant_PoT_Replicator
A script for replicating a PoT curriculum's sample databases into a person's individual Cloudant account

	
### Example Source Document format is:
	{
	  "_id": "sources",
	  "PoTs": {
	   "cloudant": [],
	   "dashdb": [
	    "https://redbookid.cloudant.com/retaildemo-visitor",
	    "https://redbookid.cloudant.com/retaildemo-store",
	    "https://redbookid.cloudant.com/retaildemo-dept",
	    "https://redbookid.cloudant.com/retaildemo-desk",
	    "https://redbookid.cloudant.com/retaildemo-slot"
	    ],
	   "watson analytics": [],
	   "BI on Cloud": []
	  }
	}
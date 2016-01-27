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
=======
## A script for replicating a PoT curriculum's sample databases into a person's individual Cloudant account

This pything script should be loaded into the virtual machine image for all PoT's which use Cloudant.
Any steps in the workbook which refer to the replication UI should be removed and replaced with directions to run this script.
Any updates to the list of databases for each PoT can be handled by contacting Brad Bonn.  He will either make the changes directly, or add appropriate permissions to anyone who handles PoT curriculum to change the referring document themselves.


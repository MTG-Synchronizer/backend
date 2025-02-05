# Getting Started  

Follow these steps to set up and run the backend:  

### 1. Add Required Files  
Place the following files in the root directory:  
- `.env` (contains environment variables)  
- `service-account.json` (used for authentication)  

### 2. Build and Run Docker Containers  
Use Docker Compose to build and start the Backend API and Neo4j database:  
```sh
docker-compose build  
docker-compose up  
```  

### 3. Run Ingest Scripts  
The following scripts process and load data into the database.  

#### **A. Scryfall Bulk Data Ingest**  
- **Script:** [`scryfall_bulk_data_injest.py`](src/db_processing/scryfall_bulk_data_injest.py)  
- **Purpose:** Fetches bulk card data from the [Scryfall API](https://scryfall.com/) and creates or updates Card Nodes in the database.  

#### **B. MTG Goldfish Decklist Processing**  
- **Script:** [`mtg_goldfish_decklist.py`](src/db_processing/mtg_goldfish_decklist.py)  
- **Setup:**  
  - Add the required `custom.json` and `metagame.json` files to the `data/mtg_goldfish` folder.  
  - These files can be scraped using the [prototyping](https://github.com/MTG-Synchronizer/prototyping) repository.  
- **Purpose:**  
  - Uses scraped deck data from [MTG Goldfish](https://www.mtggoldfish.com/) to assign sync scores between cards.  
  - The **sync score** represents how well two cards synchronize.  

💡 *Currently, only MTG Goldfish data is supported. If additional data sources are added, ensure all scraped deck data is ingested before running new ingest scripts.*  

#### **C. Set Relationships**  
- **Script:** [`set_relationships.py`](src/db_processing/set_relationships.py)  
- **Purpose:**  
  - Cleans up card node relationships.  
  - Sets the `total_recurrences` property for each card.  
  - Applies **square root scaling** to adjust the `dynamicWeight` property, dampening the effect of dividing sync by total recurrences.  

#### **D. Create Clusters**  
- **Script:** [`create_clusters.py`](src/db_processing/create_clusters.py)  
- **Purpose:** Uses the **Louvain algorithm** to identify clusters of cards that work well together based on the `dynamicWeight` property.  
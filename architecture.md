flowchart LR
    %% Define the User subgraph
    subgraph userSubgraph["User"]
        A["User (Browser)"]
    end

    %% Define the Frontend subgraph
    subgraph frontend["Frontend (React)"]
        B["UI Components"]
    end

    %% Define the Backend subgraph
    subgraph backend["Backend (Monolithic)"]
        C["API Endpoints"]
        %% Define backend modules
        subgraph modules["Modules"]
            D["User Module"]
            E["Problem Module"]
            F["Conversation Module (LLM)"]
        end
        G["Database / Data Store"]
        H["LLM Integration"]
    end

    %% Flow of Calls/Data
    A --> B
    B --> C
    C --> D
    C --> E
    C --> F
    D --> G
    E --> G
    F --> H
    H --> F
    C --> B

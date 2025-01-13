import { useState } from "react";
import { Box, TextField, Button } from "@mui/material";
import axios from "axios";

const endpointMapping = {
  Notion: "notion",
  Airtable: "airtable",
  Hubspot: "hubspot",
};

export const DataForm = ({ integrationType, credentials }) => {
  const [loadedData, setLoadedData] = useState(null);
  const endpoint = endpointMapping[integrationType];
  console.log("endpt", endpoint);
  console.log("integrationTtpe", integrationType);

  const handleLoad = async () => {
    try {
      const formData = new FormData();
      formData.append("credentials", JSON.stringify(credentials));

      const response = await axios.post(
        `http://localhost:8000/integrations/${endpoint}/load`,
        formData
      );
      const data = response.data;
      console.log("data", data);
      setLoadedData(data);
    } catch (e) {
      alert(e?.response?.data?.detail);
    }
  };

  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      flexDirection="column"
      width="100%"
    >
      <Box display="flex" flexDirection="column" width="100%">
        <TextField
          label="Loaded Data"
          value={loadedData ? JSON.stringify(loadedData, null, 2) : ""}
          sx={{
            mt: 2,
            width: "100%",
            height: "100%",
            "& .MuiInputBase-input": { color: "black" }, // Text color
            "& .MuiInputLabel-root": { color: "black" },
            "& .MuiOutlinedInput-root": {
              "& fieldset": { borderColor: "black" },
            },
          }}
          InputLabelProps={{ shrink: true }}
          multiline
          disabled
          rows={10}
          variant="outlined"
        />

        <Button onClick={handleLoad} sx={{ mt: 2 }} variant="contained">
          Load Data
        </Button>
        <Button
          onClick={() => setLoadedData(null)}
          sx={{ mt: 1 }}
          variant="contained"
        >
          Clear Data
        </Button>
      </Box>
    </Box>
  );
};

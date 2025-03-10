import React from "react";
import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Grid from '@mui/material/Grid2';
import Container from "@mui/material/Container";



const ApplicationBar = () => {


  return (
      <Container sx={{
          alignItems: 'center',
          width: "80%",
          padding: "10px"
        }}>
          <Grid container spacing={2} style={{justifyContent: "center"}} size={{md: 10, lg: 8, xl: 6}}>
                  <AppBar position="static" style={{backgroundColor: 'grey'}}>
                    <Toolbar>
                    </Toolbar>
                  </AppBar>
          </Grid>
          </Container>
  );
};

export default ApplicationBar;

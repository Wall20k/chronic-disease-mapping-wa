# Turn script into an interactive web app.
library(shiny)

# Load dplyr for data wrangling.
# We use this for selecting columns, joining tables, and creating new variables.
library(dplyr)

# Load leaflet for the interactive map.
# This package draws the clickable zoom map feature in the app.
library(leaflet)

# Load sf for spatial data.
# sf stores map shapes like the census tract boundaries.
library(sf)

# Load htmltools for custom HTML in UI text and popups.
library(htmltools)

# Load scales for nicer number formatting.
# We use it for things like comma formatting and percentage display (Used A.I to assist in scale formatting for UI).
library(scales)

# Load purrr for helper functions like map_chr() and map_dbl().
# These help loop through values in a tidy way (Important due to increased processing stress when running program).
library(purrr)

# Load tibble for small clean lookup tables.
library(tibble)


#---------------------
# This lets the app look for files inside the app folder instead of using a personal path.
app_dir <- getwd()

# The app expects the CSV to be stored in the same folder as app.R.
data_path <- file.path(app_dir, "places_wa_clean.csv")

# Create the full file path for the saved Washington tract geometry file.
# This saved file helps the app load faster and avoids re-downloading shapes every time (Again, helps with processing speed and lag).
tract_cache_path <- file.path(app_dir, "data", "wa_tracts_2023.rds")


#----------------------
# Helper function to simplify tract boundaries.
# This makes the polygons lighter and helps the map run faster (Another processing fix).
simplify_tracts <- function(tracts_sf) {
  tracts_sf %>%

    # Convert to a projected coordinate system first.
    # Simplifying geometry usually behaves better in projected coordinates.
    st_transform(3857) %>%

    # Simplify the shapes by removing some extra boundary detail.
    # dTolerance controls how aggressive the simplification is.
    # preserveTopology = TRUE helps keep the shapes from breaking.
    st_simplify(dTolerance = 80, preserveTopology = TRUE) %>%

    # Convert back to EPSG 4326 for leaflet.
    st_transform(4326)
}


#------------------------
# Display Names and Listing
variable_groups <- list(
  "Health Outcomes" = c(
    diabetes_crude_prev = "Diabetes crude prevalence",
    obesity_crude_prev = "Obesity crude prevalence",
    bphigh_crude_prev = "High blood pressure crude prevalence"
  ),
  "Health Behaviors" = c(
    csmoking_crude_prev = "Current smoking crude prevalence",
    lpa_crude_prev = "Physical inactivity crude prevalence"
  ),
  "Access to Care / Prevention" = c(
    checkup_crude_prev = "Routine checkup crude prevalence",
    access2_crude_prev = "Lack of health insurance crude prevalence"
  )
)

# Turn the grouped variable list into a simple look-up table.
# This makes it easier to: match a variable name to its label and know which group a variable belongs to
variable_lookup <- tibble::tibble(
  variable = unlist(lapply(variable_groups, names), use.names = FALSE),
  label = unlist(variable_groups, use.names = FALSE),
  group = rep(names(variable_groups), lengths(variable_groups))
)


#-----------------------------
# Define a small helper function for check-box choices (first interactice option).
# Shiny check-box inputs want a named vector...
# - the displayed text should be the readable label.
# - the stored value should be the real variable name!!!
to_choices <- function(group_name) {

  # Pull out one variable group from the list above.
  group_values <- variable_groups[[group_name]]

  # Flip the names so the UI shows readable labels but stores the actual column names as the selected values.
  stats::setNames(names(group_values), unname(group_values))
}


#------------------------------
# MAP tract work
# tract_fips is kept as character text so it matches the GEOID format from Census tracts.
places_subset <- read.csv(data_path, colClasses = c(tract_fips = "character")) %>%

  # Keep only the columns used in the final app.
  # transmute() will keep only the columns listed here and can also rename or change them.
  transmute(
    county_name,

    # Convert county_fips to character to keep identifier types consistent.
    county_fips = as.character(county_fips),

    tract_fips = tract_fips,
    diabetes_crude_prev,
    obesity_crude_prev,
    bphigh_crude_prev,
    csmoking_crude_prev,
    lpa_crude_prev,
    checkup_crude_prev,
    access2_crude_prev
  )


# Read the saved Washington tract geometry file, then simplify it for better performance.
wa_tracts <- readRDS(tract_cache_path) %>%
  simplify_tracts()

# Create one outline polygon for the entire state of Washington.
# st_union() combines all tract boundaries into one overall state shape.
wa_outline <- wa_tracts %>%
  summarise(geometry = st_union(geometry))

# Get the bounding box of Washington.
# This is used to zoom the leaflet map so it fits Washington only (remove unnecessary world mapping around WA).
wa_bbox <- sf::st_bbox(wa_outline)

# Join the PLACES data onto the tract shapes.
# GEOID comes from the tract geometry.
# tract_fips comes from the health dataset.
map_data <- wa_tracts %>%
  left_join(places_subset, by = c("GEOID" = "tract_fips")) %>%
  mutate(

    # If county name is missing after the join, label it clearly (Important for text pops).
    county_name = coalesce(county_name, "No PLACES data"),

    # Create a logical column that says whether this tract has any PLACES values at all.
    # if_all(..., is.na) ths checks if all selected variables are missing.
    # We used ! to flip that, so TRUE means "has at least some data".
    has_places_data = !if_all(all_of(variable_lookup$variable), is.na)
  )


#----------------------------------
# Obtain stats for upcoming slider interactive option
# Build a summary table with the range statistics for each variable.
# These values are used to create the sliders and the visual guide under each slider.
value_ranges <- variable_lookup %>%

  # rowwise() performs mutate() code once for each variable row.
  rowwise() %>%
  mutate(

    min_value = min(places_subset[[variable]], na.rm = TRUE),

    q1_value = as.numeric(stats::quantile(places_subset[[variable]], probs = 0.25, na.rm = TRUE, names = FALSE)),

    mean_value = mean(places_subset[[variable]], na.rm = TRUE),

    q3_value = as.numeric(stats::quantile(places_subset[[variable]], probs = 0.75, na.rm = TRUE, names = FALSE)),

    max_value = max(places_subset[[variable]], na.rm = TRUE)
  ) %>%

  # Return to a normal data frame after the rowwise work is finished.
  ungroup()


# Define a helper function that converts one numeric value into a percent.
# This is used to place the Min / Q1 / Mean / Q3 / Max markers along the slider guide for added detail.
stat_position <- function(value, min_value, max_value) {
  # Compute the relative position and force it to stay between 0 and 100.
  pmin(100, pmax(0, 100 * (value - min_value) / (max_value - min_value)))
}


#--------------------------------
# Create Slider
# Define a helper function that creates the little visual guide under each slider.
# The guide shows where Min, Q1, Mean, Q3, and Max fall across each variable's range.
build_slider_guide <- function(range_row) {

  # Build a small table with the stats that should appear in the guide.
  stats_tbl <- tibble(
    stat = c("Min", "Q1", "Mean", "Q3", "Max"),
    value = c(
      range_row$min_value,
      range_row$q1_value,
      range_row$mean_value,
      range_row$q3_value,
      range_row$max_value
    ),

    color = c("darkgrey", "lightgreen", "orange", "lightgreen", "darkgrey"),

    # Use slightly different vertical positions so nearby labels do not overlap as much.
    label_top = c(34, 56, 34, 56, 34)
  ) %>%

    # Convert each statistic value into a left position on the 0 to 100 guide scale.
    mutate(position = purrr::map_dbl(value, ~ stat_position(.x, range_row$min_value, range_row$max_value)))


  # Create the vertical tick marks for the guide (visually helpful).
  marker_nodes <- lapply(seq_len(nrow(stats_tbl)), function(i) {
    tags$div(
      class = "slider-guide-marker",
      style = sprintf(
        "left: %.2f%%; border-color: %s;",
        stats_tbl$position[i],
        stats_tbl$color[i]
      ),

      # title adds hover text in the browser.
      title = sprintf("%s: %.1f%%", stats_tbl$stat[i], stats_tbl$value[i])
    )
  })


  # Create the text labels under the tick marks.
  label_nodes <- lapply(seq_len(nrow(stats_tbl)), function(i) {
    tags$div(
      class = "slider-guide-label",
      style = sprintf("left: %.2f%%; top: %dpx;", stats_tbl$position[i], stats_tbl$label_top[i]),
      HTML(sprintf("<strong>%s</strong><br/>%.1f%%", stats_tbl$stat[i], stats_tbl$value[i]))
    )
  })


  # Return one HTML block that contains the track, markers, and labels.
  tags$div(
    class = "slider-guide-wrap",
    tags$div(class = "slider-guide-track"),
    marker_nodes,
    label_nodes
  )
}


#------------------------------
# MAP tract pop-ups
# Define a helper function that builds the popup HTML for one tract.
# The popup appears when a user clicks a tract on the map.
build_popup <- function(data, selected_vars) {

  # If no variables are currently selected, show all variables in the popup.
  # Otherwise show only the selected variables.
  fields_to_show <- if (length(selected_vars) == 0) variable_lookup$variable else selected_vars


  # Create one popup row for each variable that should be shown.
  popup_rows <- purrr::map_chr(fields_to_show, function(var_name) {

    # Find the readable label for this variable name.
    label <- variable_lookup$label[match(var_name, variable_lookup$variable)]

    # Pull the actual value.
    value <- data[[var_name]]

    # If the value is missing, say "No data".
    # Otherwise format it as a percent with one decimal place.
    formatted_value <- ifelse(is.na(value), "No data", paste0(number(value, accuracy = 0.1), "%"))

    # Combine the label and the formatted value into one HTML line.
    paste0("<strong>", label, ":</strong> ", formatted_value)
  })


  # Combine tract name, county, GEOID, and variable rows into one popup (THIS is what we see on the map).
  paste0(
    "<strong>", data[["NAMELSAD"]], "</strong><br/>",
    "<strong>County:</strong> ", data[["county_name"]], "<br/>",
    "<strong>Tract GEOID:</strong> ", data[["GEOID"]], "<br/>",
    paste(popup_rows, collapse = "<br/>")
  )
}


#---------------------------------
# UI
# Build the visible layout of the app.
ui <- fluidPage(

  # Set a Bootstrap theme for colors and fonts.
  theme = bslib::bs_theme(
    bg = "beige",
    fg = "black",
    primary = "#990000",
    secondary = "darkgrey",
    base_font = bslib::font_google("Source Sans 3"),
    heading_font = bslib::font_google("Merriweather")
  ),


  # AI assistance in adding custom CSS to control the look of the app.
  tags$head(
    tags$style(HTML("
      .app-title { margin-bottom: 0.25rem; }
      .app-subtitle { color: #52656b; margin-bottom: 1rem; }
      .control-card {
        background: #fffdf8;
        border: 1px solid #d9d2c1;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 8px 18px rgba(31, 42, 48, 0.06);
      }
      .control-card h4 {
        margin-top: 0;
        margin-bottom: 10px;
        color: #23404a;
      }
      .stat-strip {
        background: linear-gradient(135deg, #005f73 0%, #0a9396 100%);
        color: white;
        border-radius: 14px;
        padding: 14px 18px;
        margin-bottom: 16px;
      }
      .leaflet-container {
        background: #f7f5ef;
      }
      .help-note {
        color: #5d6f74;
        font-size: 0.95rem;
      }
      .slider-block {
        margin-bottom: 22px;
      }
      .slider-guide-wrap {
        position: relative;
        height: 76px;
        margin-top: 6px;
      }
      .slider-guide-track {
        position: absolute;
        left: 0;
        right: 0;
        top: 16px;
        height: 8px;
        border-radius: 999px;
        background: linear-gradient(90deg, #d9d2c1 0%, #c7ddd3 25%, #9ec2c8 50%, #c7ddd3 75%, #d9d2c1 100%);
      }
      .slider-guide-marker {
        position: absolute;
        top: 8px;
        width: 0;
        height: 22px;
        border-left: 3px solid;
        transform: translateX(-50%);
      }
      .slider-guide-label {
        position: absolute;
        transform: translateX(-50%);
        text-align: center;
        font-size: 0.66rem;
        color: #41565d;
        line-height: 1.15;
        white-space: nowrap;
      }
    "))
  ),


  # Display the app title and sub title.
  titlePanel(
    div(
      class = "app-title",
      "Washington CDC-PLACES Layered Health Map"
    )
  ),

  div(
    class = "app-subtitle",
    "Select one or more variables from the three analysis groups. A tract is highlighted only if it meets every active slider range at the same time."
  ),


  # Create a sidebar layout: left side = controls | right side = summary + map
  sidebarLayout(
    sidebarPanel(
      width = 4,

      # First control card: variable selection check-boxes
      div(
        class = "control-card",
        h4("Variable Selection"),

        checkboxGroupInput(
          "health_outcomes",
          "Health Outcomes",
          choices = to_choices("Health Outcomes"),
          selected = c("diabetes_crude_prev")
        ),

        checkboxGroupInput(
          "health_behaviors",
          "Health Behaviors",
          choices = to_choices("Health Behaviors"),
          selected = c("lpa_crude_prev")
        ),

        checkboxGroupInput(
          "prevention",
          "Access to Care / Prevention",
          choices = to_choices("Access to Care / Prevention"),
          selected = c("access2_crude_prev")
        )
      ),

      # Second control card: sliders for selected variables
      div(
        class = "control-card",
        h4("Selected Variable Ranges"),

        # uiOutput means the sliders will be built dynamically in the server.
        # This is necessary because the number of sliders changes depending on which variables are selected.
        uiOutput("slider_controls"),

        div(
          class = "help-note",
          "Each slider uses the observed range in the Washington PLACES tract dataset. Inclusive ranges are applied to all selected variables."
        )
      ),

      # Third control card: plain-language map rule explanation
      div(
        class = "control-card",
        h4("Map Rules"),
        tags$p("Tracts highlighted in crimson satisfy every selected slider condition."),
        tags$p("Tracts highlighted in beige either fail at least one condition or do not have PLACES values for one of the selected variables.")
      )
    ),


    # Main panel on the right side
    mainPanel(
      width = 8,

      # Summary strip showing the number of matching tracts and active filters
      div(class = "stat-strip", htmlOutput("match_summary")),

      # The leaflet map output
      leafletOutput("burden_map", height = 760)
    )
  )
)


#----------------------------------
# Server logic
# Define the server side of the app.
server <- function(input, output, session) {

  # Combine selections from the three check-box groups into one unique vector.
  selected_vars <- reactive({
    unique(c(input$health_outcomes, input$health_behaviors, input$prevention))
  })


  # Create one reactive object that stores:the selected variables and the slider ranges for those variables
  filter_state <- reactive({
    vars <- selected_vars()

    # Build a named list where each selected variable points to its slider values.
    ranges <- stats::setNames(
      lapply(vars, function(var_name) input[[paste0("range_", var_name)]]),
      vars
    )

    list(vars = vars, ranges = ranges)
  }) %>%

    # debounce waits a short moment before updating.
    # This helps prevent repeated rapid redraws while the user is dragging sliders (This was causing R to crash).
    debounce(350)


  # Build the slider UI for only the currently selected variables.
  output$slider_controls <- renderUI({
    vars <- selected_vars()

    # If no variables are selected, show a message instead of sliders.
    if (length(vars) == 0) {
      return(tags$p("Choose at least one variable to activate a prevalence slider."))
    }

    # Create one slider block per selected variable.
    sliders <- lapply(vars, function(var_name) {

      # Pull the summary stats for this variable so we know its distribution and guide values.
      range_row <- value_ranges %>% filter(variable == var_name)

      tags$div(
        class = "slider-block",

        # Create the actual slider input.
        sliderInput(
          inputId = paste0("range_", var_name),
          label = range_row$label,
          min = range_row$min_value,
          max = range_row$max_value,
          value = c(range_row$min_value, range_row$max_value),
          step = 0.1,
          sep = "",
          post = "%"
        ),

        # Add the visual guide under the slider.
        build_slider_guide(range_row)
      )
    })

    # Combine all slider blocks into one UI output.
    tagList(sliders)
  })


  # Filter the map data based on all selected slider conditions.
  filtered_map_data <- reactive({
    state <- filter_state()
    vars <- state$vars
    data <- map_data

    # If no variables are selected, just mark tracts with data as matching.
    if (length(vars) == 0) {
      return(data %>% mutate(matches_all = has_places_data))
    }

    # Start by assuming that every tract matches.
    data$matches_all <- TRUE

    # For each selected variable, keep only tracts that are inside that slider's range.
    for (var_name in vars) {
      slider_values <- state$ranges[[var_name]]

      # If the slider is not ready yet, skip it for this moment (fixed an error with slider values being used before slider was running).
      if (is.null(slider_values)) {
        next
      }

      # Update the matches_all column so a tract stays TRUE only if it passes every condition.
      data$matches_all <- data$matches_all &
        !is.na(data[[var_name]]) &
        data[[var_name]] >= slider_values[1] &
        data[[var_name]] <= slider_values[2]
    }

    data
  })


  # Create text summary above the map.
  output$match_summary <- renderUI({
    data <- filtered_map_data()

    # Count how many tracts match the current filter.
    matched_n <- sum(data$matches_all, na.rm = TRUE)

    # Count how many tracts have any PLACES data available at all (total).
    available_n <- sum(data$has_places_data, na.rm = TRUE)

    vars <- selected_vars()

    # Build readable text showing which variables are active.
    selected_labels <- if (length(vars) == 0) {
      "No variables selected"
    } else {
      paste(variable_lookup$label[match(vars, variable_lookup$variable)], collapse = " | ")
    }

    # Return summary as HTML.
    HTML(
      paste0(
        "<strong>Matching tracts:</strong> ", comma(matched_n),
        " of ", comma(available_n),
        " with PLACES data",
        "<br/><strong>Active filters:</strong> ", selected_labels
      )
    )
  })


  # Create base leaflet map.
  # This runs once to set the map view to Washington State.
  output$burden_map <- renderLeaflet({
    leaflet() %>%
      fitBounds(
        lng1 = wa_bbox[["xmin"]],
        lat1 = wa_bbox[["ymin"]],
        lng2 = wa_bbox[["xmax"]],
        lat2 = wa_bbox[["ymax"]]
      )
  })


  # Observe filter changes and update the existing map.
  observe({
    data <- filtered_map_data()

    # Remove geometry temporarily so popup text can be built more easily row by row.
    popup_source <- sf::st_drop_geometry(data)

    active_vars <- filter_state()$vars

    # Build one popup string for every tract.
    popup_text <- vapply(
      seq_len(nrow(popup_source)),
      function(i) build_popup(as.list(popup_source[i, , drop = FALSE]), active_vars),
      character(1)
    )

    # Create a fill group used for coloring.
    data$fill_group <- ifelse(
      data$matches_all,
      "Meets all selected conditions",
      "Does not meet all selected conditions"
    )

    # Store the popup text with the map data.
    data$popup_text <- popup_text

    # Create a color palette:
    # gray = does not match
    # orange = matches all selected conditions
    pal <- colorFactor(
      palette = c("beige", "#990000"),
      domain = data$fill_group
    )


    # Use leafletProxy to update the existing map instead of rebuilding it from scratch.
    # This is faster and helps reduce our lag issue.
    leafletProxy("burden_map", data = data) %>%

      # Remove old polygons.
      clearShapes() %>%

      # Remove old legend.
      clearControls() %>%

      # Draw Washington outline first.
      addPolygons(
        data = wa_outline,
        fill = FALSE,
        color = "black",
        weight = 1.2,
        opacity = 0.9,
        smoothFactor = 0.2
      ) %>%

      # Draw all tract polygons on top.
      addPolygons(
        fillColor = ~pal(fill_group),
        fillOpacity = 0.8,
        color = "black",
        weight = 0.35,
        opacity = 0.6,
        smoothFactor = 0.2,
        popup = ~popup_text,
        label = ~paste0(NAMELSAD, " | ", county_name)
      ) %>%

      # Add legend so users know what the colors mean.
      addLegend(
        position = "bottomright",
        pal = pal,
        values = ~fill_group,
        opacity = 0.9,
        title = "Combined variable filter"
      )
  })
}


# Launch the app.
shinyApp(ui = ui, server = server)

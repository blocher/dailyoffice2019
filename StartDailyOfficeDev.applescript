-- Get screen dimensions
tell application "Finder"
    set screenBounds to bounds of window of desktop
    set screenWidth to item 3 of screenBounds
    set screenHeight to item 4 of screenBounds
end tell

tell application "iTerm"
    activate
    
    -- Close any existing windows with our specific session names to avoid duplicates
    set windowList to windows
    repeat with w in windowList
        try
            set sessionList to sessions of current tab of w
            repeat with s in sessionList
                tell s
                    set doSession to variable named "user.DailyOfficeSession"
                    if doSession is not missing value then
                        close w
                        exit repeat
                    end if
                end tell
            end repeat
        end try
    end repeat
    
    -- Create new window and set its bounds (75% width, 100% height)
    set newWindow to (create window with default profile)
    set bounds of newWindow to {0, 0, screenWidth * 0.75, screenHeight}
    
    -- Window 1 (Top Pane): Site
    tell current session of newWindow
        set variable named "user.DailyOfficeSession" to "Backend"
        set name to "Daily Office Backend"
        write text "source ~/projects/dailyoffice2019/env/bin/activate"
        write text "cd ~/projects/dailyoffice2019/site"
        write text "kill $(lsof -t -i:8000) 2>/dev/null || true"
        write text "python manage.py runsslserver"
        set pane2 to (split horizontally with default profile)
    end tell
    
    -- Window 2 (Middle Pane): App
    tell pane2
        set variable named "user.DailyOfficeSession" to "Frontend"
        set name to "Daily Office Frontend"
        write text "source ~/projects/dailyoffice2019/env/bin/activate"
        write text "cd ~/projects/dailyoffice2019/app"
        write text "kill $(lsof -t -i:5173) 2>/dev/null || true"
        write text "npm run dev"
        set pane3 to (split horizontally with default profile)
    end tell
    
    -- Window 3 (Bottom Pane): Root
    tell pane3
        set variable named "user.DailyOfficeSession" to "Working"
        set name to "Daily Office Working Session"
        write text "source ~/projects/dailyoffice2019/env/bin/activate"
        write text "cd ~/projects/dailyoffice2019"
        write text "git status"
    end tell
end tell

-- Pre-accept the development certificate in macOS Keychain for Chrome
-- We extract the SHA1 fingerprint of the certificate and check if it already exists in the keychain
-- This prevents the "You are making changes to your Certificate Trust Settings" prompt on every run
try
    do shell script "cert_path=$(find ~/projects/dailyoffice2019 -type d \\( -name node_modules -o -name .git \\) -prune -o -name development.crt -print | head -n 1); if [ -n \"$cert_path\" ]; then hash=$(openssl x509 -noout -fingerprint -sha1 -in \"$cert_path\" | cut -d= -f2 | tr -d :); if ! security find-certificate -a -Z | grep -q \"$hash\"; then security add-trusted-cert -r trustRoot -k ~/Library/Keychains/login.keychain-db \"$cert_path\"; fi; fi > /dev/null 2>&1 &"
end try

-- Open Chrome to the dev server in the background so it doesn't hang the script
try
    do shell script "open -a 'Google Chrome' 'http://localhost:5173/' > /dev/null 2>&1 &"
end try

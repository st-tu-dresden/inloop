if ! grep -q DJANGO_SETTINGS_MODULE ~/.profile; then
    echo "export DJANGO_SETTINGS_MODULE=inloop.settings.production" | tee -a ~/.profile
fi

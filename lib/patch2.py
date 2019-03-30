import sys
from . import environments as env



def apply():
    sys.modules['instapy'].InstaPy.like_by_locations.__code__ = like_by_locations_patch.__code__


def like_by_locations_patch(self,
                      locations=None,
                      amount=50,
                      media=None,
                      skip_top_posts=True):
    """Likes (default) 50 images per given locations"""
    if self.aborting:
        return self

    liked_img = 0
    already_liked = 0
    inap_img = 0
    commented = 0
    followed = 0
    not_valid_users = 0

    locations = locations or []
    self.quotient_breach = False

    for index, location in enumerate(locations):
        if self.quotient_breach:
            break

        self.logger.info('Location [{}/{}]'
                         .format(index + 1, len(locations)))
        self.logger.info('--> {}'.format(location.encode('utf-8')))

        try:
            links2 = get_links_for_location(self.browser,
                                           location,
                                           10,
                                           self.logger,
                                           media,
                                           skip_top_posts)
            random.shuffle(links2)
            links = links2[:1]
        except NoSuchElementException as exc:
            self.logger.warning(
                "Error occurred while getting images from location: {}  "
                "~maybe too few images exist\n\t{}\n".format(location, str(
                    exc).encode("utf-8")))
            continue

        for i, link in enumerate(links):
            if self.jumps["consequent"]["likes"] >= self.jumps["limit"][
                "likes"]:
                self.logger.warning(
                    "--> Like quotient reached its peak!\t~leaving "
                    "Like-By-Locations activity\n")
                self.quotient_breach = True
                # reset jump counter after a breach report
                self.jumps["consequent"]["likes"] = 0
                break

            self.logger.info('[{}/{}]'.format(i + 1, len(links)))
            self.logger.info(link)

            try:
                inappropriate, user_name, is_video, reason, scope = (
                    check_link(self.browser,
                               link,
                               self.dont_like,
                               self.mandatory_words,
                               self.mandatory_language,
                               self.is_mandatory_character,
                               self.mandatory_character,
                               self.check_character_set,
                               self.ignore_if_contains,
                               self.logger))

                if not inappropriate and self.delimit_liking:
                    self.liking_approved = verify_liking(self.browser,
                                                         self.max_likes,
                                                         self.min_likes,
                                                         self.logger)

                if not inappropriate and self.liking_approved:
                    # validate user
                    validation, details = self.validate_user_call(
                        user_name)

                    if validation is not True:
                        self.logger.info(
                            "--> Not a valid user: {}".format(details))
                        not_valid_users += 1
                        continue
                    else:
                        web_address_navigator(self.browser, link)

                    # try to like
                    like_state, msg = like_image(self.browser,
                                                 user_name,
                                                 self.blacklist,
                                                 self.logger,
                                                 self.logfolder)

                    if like_state is True:
                        liked_img += 1
                        # reset jump counter after a successful like
                        self.jumps["consequent"]["likes"] = 0

                        checked_img = True
                        temp_comments = []

                        commenting = random.randint(
                            0, 100) <= self.comment_percentage
                        following = random.randint(
                            0, 100) <= self.follow_percentage

                        if self.use_clarifai and (following or commenting):
                            try:
                                checked_img, temp_comments, \
                                clarifai_tags = (
                                    self.query_clarifai())

                            except Exception as err:
                                self.logger.error(
                                    'Image check error: {}'.format(err))

                        # comments
                        if (self.do_comment and
                                user_name not in self.dont_include and
                                checked_img and
                                commenting):

                            if self.delimit_commenting:
                                (self.commenting_approved,
                                 disapproval_reason) = verify_commenting(
                                    self.browser,
                                    self.max_comments,
                                    self.min_comments,
                                    self.comments_mandatory_words,
                                    self.logger)
                            if self.commenting_approved:
                                # smart commenting
                                comments = self.fetch_smart_comments(
                                    is_video,
                                    temp_comments)
                                if comments:
                                    comment_state, msg = comment_image(
                                        self.browser,
                                        user_name,
                                        comments,
                                        self.blacklist,
                                        self.logger,
                                        self.logfolder)
                                    if comment_state is True:
                                        commented += 1

                            else:
                                self.logger.info(disapproval_reason)

                        else:
                            self.logger.info('--> Not commented')
                            sleep(1)

                        # following
                        if (self.do_follow and
                                user_name not in self.dont_include and
                                checked_img and
                                following and
                                not follow_restriction("read", user_name,
                                                       self.follow_times,
                                                       self.logger)):

                            follow_state, msg = follow_user(self.browser,
                                                            "post",
                                                            self.username,
                                                            user_name,
                                                            None,
                                                            self.blacklist,
                                                            self.logger,
                                                            self.logfolder)
                            if follow_state is True:
                                followed += 1

                        else:
                            self.logger.info('--> Not following')
                            sleep(1)

                    elif msg == "already liked":
                        already_liked += 1

                    elif msg == "jumped":
                        # will break the loop after certain consecutive
                        # jumps
                        self.jumps["consequent"]["likes"] += 1

                else:
                    self.logger.info(
                        '--> Image not liked: {}'.format(
                            reason.encode('utf-8')))
                    inap_img += 1

            except NoSuchElementException as err:
                self.logger.error('Invalid Page: {}'.format(err))

        self.logger.info('Location: {}'.format(location.encode('utf-8')))
        self.logger.info('Liked: {}'.format(liked_img))
        self.logger.info('Already Liked: {}'.format(already_liked))
        self.logger.info('Commented: {}'.format(commented))
        self.logger.info('Followed: {}'.format(followed))
        self.logger.info('Inappropriate: {}'.format(inap_img))
        self.logger.info('Not valid users: {}\n'.format(not_valid_users))

    self.followed += followed
    self.liked_img += liked_img
    self.already_liked += already_liked
    self.commented += commented
    self.inap_img += inap_img
    self.not_valid_users += not_valid_users

    return self

